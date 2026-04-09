import streamlit as st
from api_client import (create_chat, list_chats, rename_chat,
                         delete_chat, get_messages, ingest, stream_chat)

st.set_page_config(page_title="Ollama Chat", page_icon="🤖", layout="wide")

# ── Bootstrap session ────────────────────────────────────────────────────────
if "active_chat" not in st.session_state:
    st.session_state.active_chat = None
if "messages_cache" not in st.session_state:
    st.session_state.messages_cache = {}

# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("🤖 Ollama Chat")
    st.caption("Backend: RAG + Memory + Persistent")
    st.divider()

    if st.button("＋ New Chat", use_container_width=True):
        c = create_chat()
        st.session_state.active_chat = c["chat_id"]
        st.session_state.messages_cache[c["chat_id"]] = []
        st.rerun()

    chats = list_chats()

    if not chats and not st.session_state.active_chat:
        c = create_chat()
        st.session_state.active_chat = c["chat_id"]
        st.rerun()

    st.markdown("**Conversations**")
    for chat in chats:
        cid = chat["id"]
        col1, col2 = st.columns([5, 1])
        with col1:
            label = ("▶ " if cid == st.session_state.active_chat else "") + chat["name"]
            if st.button(label, key=f"sel_{cid}", use_container_width=True):
                st.session_state.active_chat = cid
                st.session_state.messages_cache[cid] = get_messages(cid)
                st.rerun()
        with col2:
            if st.button("🗑", key=f"del_{cid}"):
                delete_chat(cid)
                if st.session_state.active_chat == cid:
                    st.session_state.active_chat = None
                st.rerun()

    st.divider()

    if st.session_state.active_chat:
        cur = next((c for c in chats if c["id"] == st.session_state.active_chat), None)
        if cur:
            new_name = st.text_input("Rename", value=cur["name"])
            if new_name != cur["name"]:
                rename_chat(st.session_state.active_chat, new_name)
                st.rerun()

        st.divider()
        st.markdown("**📎 Ingest Code / Docs**")
        uploaded = st.file_uploader("Upload file", type=["py","txt","md","js","ts","java","cpp","cs","go","rs"])
        if uploaded:
            content = uploaded.read().decode("utf-8", errors="ignore")
            with st.spinner(f"Ingesting {uploaded.name}..."):
                r = ingest(st.session_state.active_chat, content, uploaded.name)
            st.success(f"✅ {r['chunks_stored']} chunks stored")

        paste = st.text_area("Or paste code/text", height=100)
        if st.button("Ingest pasted text") and paste:
            with st.spinner("Ingesting..."):
                r = ingest(st.session_state.active_chat, paste, "pasted")
            st.success(f"✅ {r['chunks_stored']} chunks stored")

# ── Main area ────────────────────────────────────────────────────────────────
active = st.session_state.active_chat
if not active:
    st.info("Create or select a chat from the sidebar.")
    st.stop()

# Load messages if not cached
if active not in st.session_state.messages_cache:
    st.session_state.messages_cache[active] = get_messages(active)

cur_chat = next((c for c in chats if c["id"] == active), None)
st.subheader(cur_chat["name"] if cur_chat else active)
st.divider()

for msg in st.session_state.messages_cache[active]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Message… (paste 10k lines of code, ask anything)"):
    st.session_state.messages_cache[active].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        full = ""
        for token in stream_chat(active, prompt):
            full += token
            placeholder.markdown(full + "▌")
        placeholder.markdown(full)

    st.session_state.messages_cache[active].append({"role": "assistant", "content": full})