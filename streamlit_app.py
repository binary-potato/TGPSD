import streamlit as st
import json
import os
from datetime import datetime
import uuid
from PIL import Image

# Constants
MESSAGES_FILE = "messages.json"
IMAGES_DIR = "images"

# Ensure the images directory exists
if not os.path.exists(IMAGES_DIR):
    os.makedirs(IMAGES_DIR)

# Function to load tags from messages
def get_existing_tags():
    messages = load_messages()
    tags = set()
    for msg in messages:
        tags.update(msg.get('tags', []))
    return sorted(list(tags))

# Function to migrate existing messages and add IDs if missing
def migrate_messages():
    if os.path.exists(MESSAGES_FILE):
        try:
            with open(MESSAGES_FILE, "r") as f:
                messages = json.load(f)
            
            # Check if any message needs an ID
            modified = False
            for msg in messages:
                if 'id' not in msg:
                    msg['id'] = str(uuid.uuid4())
                    modified = True
                if 'comments' not in msg:
                    msg['comments'] = []
                    modified = True
            
            # Save if modifications were made
            if modified:
                with open(MESSAGES_FILE, "w") as f:
                    json.dump(messages, f, indent=4)
            
            return messages
        except (json.JSONDecodeError, ValueError):
            return []
    return []

# Function to load messages
def load_messages():
    messages = migrate_messages()  # This will ensure all messages have IDs
    return messages

# Function to save messages
def save_messages(messages):
    with open(MESSAGES_FILE, "w") as f:
        json.dump(messages, f, indent=4)

# Function to save a new message
def save_message(name, message, tags, image_filename=None):
    messages = load_messages()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    message_id = str(uuid.uuid4())
    messages.append({
        "id": message_id,
        "name": name,
        "message": message,
        "timestamp": timestamp,
        "image": image_filename,
        "tags": tags,
        "comments": []
    })
    save_messages(messages)
    return message_id

# Function to add a comment
def add_comment(message_id, commenter_name, comment_text):
    messages = load_messages()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    for msg in messages:
        if msg["id"] == message_id:
            if "comments" not in msg:
                msg["comments"] = []
            msg["comments"].append({
                "name": commenter_name,
                "comment": comment_text,
                "timestamp": timestamp
            })
            break
    
    save_messages(messages)

# Set page title and header
st.set_page_config(page_title="TGPSD", page_icon="📓", layout="wide")

# Sidebar
st.sidebar.title("TGPSD")

# Search and Filter Section in sidebar with search icon
st.sidebar.header("🔍 Search and Filter")
search_query = st.sidebar.text_input("Search messages:", "", 
    placeholder="Search by name, message, or tags...")

# Get existing tags and allow adding new ones
existing_tags = get_existing_tags()
new_tag = st.sidebar.text_input("Add a new tag:")
if new_tag and new_tag not in existing_tags:
    existing_tags.append(new_tag)
selected_tags = st.sidebar.multiselect("Filter by tags:", existing_tags)

# Main content
st.title("TGPSD")
st.subheader("""
For students who want to make a mark. Report false identity at chuisaac2014b@gmail.com

**How to use:**
- You can format your message using **Markdown**. For example:
  - Use `**bold**` for bold text.
  - Use `*italic*` for italic text.
  - Use `-` for lists.
  - Emojis are supported too! 🎉
- Add or create tags to categorize your message
- Comment on messages to start discussions
- Optionally, upload an image with your message (PNG, JPG, JPEG, GIF).
""")

# Create three columns for the main action buttons
col1, col2, col3 = st.columns(3)

# Initialize session state for active page if not exists
if 'active_page' not in st.session_state:
    st.session_state.active_page = None

with col1:
    if st.button("📝 Create Message", use_container_width=True):
        st.session_state.active_page = "create"

with col2:
    if st.button("🔍 Search Messages", use_container_width=True):
        st.session_state.active_page = "search"

with col3:
    if st.button("📖 View All Messages", use_container_width=True):
        st.session_state.active_page = "view"

# Handle different pages
if st.session_state.active_page == "create":
    st.markdown("### Create New Message")
    name = st.text_input("Enter your name:", max_chars=50)
    message = st.text_area("Enter your message:", height=150)
    
    # Tag selection with option to add new tags
    message_tags = st.multiselect("Select or add new tags:", existing_tags)
    new_message_tag = st.text_input("Add a new tag for this message:")
    if new_message_tag and new_message_tag not in message_tags:
        message_tags.append(new_message_tag)
    
    uploaded_image = st.file_uploader("Upload an image (optional):", type=["png", "jpg", "jpeg", "gif"])
    
    if st.button("Submit Message"):
        if not name.strip():
            st.error("Please enter your name.")
        elif not message.strip():
            st.error("Please enter a message.")
        elif not message_tags:
            st.error("Please select at least one tag.")
        else:
            image_filename = None
            if uploaded_image:
                unique_id = uuid.uuid4().hex
                file_extension = os.path.splitext(uploaded_image.name)[1]
                image_filename = f"{unique_id}{file_extension}"
                image_path = os.path.join(IMAGES_DIR, image_filename)
                
                try:
                    image = Image.open(uploaded_image)
                    image.save(image_path)
                except Exception as e:
                    st.error(f"Error saving image: {e}")
                    image_filename = None

            save_message(name, message, message_tags, image_filename)
            st.success("Message posted successfully!")
            st.session_state.active_page = "view"
            st.rerun()

# Display messages (for both search and view pages)
if st.session_state.active_page in ["search", "view"]:
    messages = load_messages()
    filtered_messages = messages

    if st.session_state.active_page == "search":
        st.markdown("### Search Results")
        if search_query:
            search_query = search_query.lower()
            filtered_messages = [
                msg for msg in filtered_messages
                if search_query in msg['name'].lower() or 
                search_query in msg['message'].lower() or 
                any(search_query in tag.lower() for tag in msg.get('tags', []))
            ]
    else:
        st.markdown("### All Messages")

    # Apply tag filter
    if selected_tags:
        filtered_messages = [
            msg for msg in filtered_messages
            if any(tag in msg.get('tags', []) for tag in selected_tags)
        ]

    if not filtered_messages:
        st.info("🔍 No messages found matching your criteria.")
    
    for msg in reversed(filtered_messages):
        with st.container():
            # Message header with name, timestamp, and tags
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"**{msg['name']}** *({msg['timestamp']})*")
            with col2:
                st.markdown(" ".join([f"`{tag}`" for tag in msg.get('tags', [])]))
            
            # Message content
            st.markdown(msg['message'])
            
            # Display image if present
            if msg.get('image'):
                image_path = os.path.join(IMAGES_DIR, msg['image'])
                if os.path.exists(image_path):
                    st.image(image_path, use_column_width=True)
            
            # Comments section
            with st.expander(f"💬 Comments ({len(msg.get('comments', []))})"):
                # Display existing comments
                for comment in msg.get('comments', []):
                    st.markdown(f"**{comment['name']}** *({comment['timestamp']})*")
                    st.markdown(f"> {comment['comment']}")
                    st.markdown("---")
                
                # Add new comment form
                with st.form(key=f"comment_form_{msg['id']}"):
                    commenter_name = st.text_input("Your name:", key=f"commenter_name_{msg['id']}")
                    comment_text = st.text_area("Add a comment:", key=f"comment_text_{msg['id']}")
                    submit_comment = st.form_submit_button("Post Comment")
                    
                    if submit_comment:
                        if not commenter_name.strip():
                            st.error("Please enter your name.")
                        elif not comment_text.strip():
                            st.error("Please enter a comment.")
                        else:
                            add_comment(msg['id'], commenter_name, comment_text)
                            st.success("Comment added successfully!")
                            st.rerun()
            
            st.markdown("---")
