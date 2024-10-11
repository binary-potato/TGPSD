import streamlit as st
import json
import os
from datetime import datetime
import uuid
from PIL import Image

# Constants
MESSAGES_FILE = "messages.json"
IMAGES_DIR = "images"

# Predefined tags for messages
TAGS = ["Question", "Announcement", "Feedback", "General", "Event", "Other"]

# Ensure the images directory exists
if not os.path.exists(IMAGES_DIR):
    os.makedirs(IMAGES_DIR)

# Function to migrate existing messages and add IDs if missing
def migrate_messages():
    if os.path.exists(MESSAGES_FILE):
        try:
            with open(MESSAGES_FILE, "r") as f:
                messages = json.load(f)
            
            # Check if any message needs an ID or visibility status
            modified = False
            for msg in messages:
                if 'id' not in msg:
                    msg['id'] = str(uuid.uuid4())
                    modified = True
                if 'comments' not in msg:
                    msg['comments'] = []
                    modified = True
                if 'visibility' not in msg:
                    msg['visibility'] = 'public'  # Default to public for existing messages
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
def save_message(name, message, tags, visibility, is_thread=False, password=None, image_filename=None):
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
        "comments": [],
        "visibility": visibility,
        "is_thread": is_thread,  # Indicates if this is a thread
        "password": password  # Store password for private threads
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

# Set page title and header with slogan
st.set_page_config(page_title="TGPSD", page_icon="📓", layout="centered")


st.title("TGPSD")
st.subheader("""For students who want to make a mark.""")
st.markdown("""
**How to use:**
- You can format your message using Markdown. For example:
- Use `**bold**` for bold text.
- Use `*italic*` for italic text.
- Use - for lists.
- Emojis are supported too! 🎉
- Add tags to categorize your message.
- Comment on messages to start discussions.
- Optionally, upload an image with your message (PNG, JPG, JPEG, GIF).
- Create public threads visible to everyone or private threads for specific discussions.
""")

# Search and Filter Section in sidebar with search icon
st.sidebar.header("🔍 Search and Filter")
search_query = st.sidebar.text_input("Search messages:", "", 
    placeholder="Search by name, message, or tags...")
selected_tags = st.sidebar.multiselect("Filter by tags:", TAGS)
visibility_filter = st.sidebar.radio("Show threads:", ["All", "Public Only", "Private Only"])

# Two buttons for creating different types of threads
col1, col2 = st.columns(2)
with col1:
    if st.button("🌍 Create Public Thread", use_container_width=True):
        st.session_state.creating_thread = "public"
with col2:
    if st.button("🔒 Create Private Thread", use_container_width=True):
        st.session_state.creating_thread = "private"

# Message Submission Form for General Messages
with st.form(key='general_message_form'):
    st.markdown("### Post a General Message")
    name = st.text_input("Enter your name:", max_chars=50)
    message = st.text_area("Enter your message:", height=150)
    message_tags = st.multiselect("Select tags for your message:", TAGS)
    uploaded_image = st.file_uploader("Upload an image (optional):", type=["png", "jpg", "jpeg", "gif"])
    
    submit_general_message = st.form_submit_button(label='Submit General Message')
    
    if submit_general_message:
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

            # Save the general message
            save_message(name, message, message_tags, 'public', False, None, image_filename)
            st.success("General message created successfully!")

# Message Submission Form for Threads
if hasattr(st.session_state, 'creating_thread'):
    thread_visibility = st.session_state.creating_thread
    with st.form(key='thread_form'):
        st.markdown(f"### Create New {'Public' if thread_visibility == 'public' else 'Private'} Thread")
        name = st.text_input("Enter your name:", max_chars=50)
        message = st.text_area("Enter your message:", height=150)
        message_tags = st.multiselect("Select tags for your message:", TAGS)
        uploaded_image = st.file_uploader("Upload an image (optional):", type=["png", "jpg", "jpeg", "gif"])
        thread_password = None
        
        # If creating a private thread, show password input field
        if thread_visibility == 'private':
            thread_password = st.text_input("Set a password for the private thread (optional):", type="password")
        
        submit_thread = st.form_submit_button(label='Submit Thread')
        cancel_button = st.form_submit_button(label='Cancel')

        if cancel_button:
            del st.session_state.creating_thread
            st.stop()  # Use stop() instead of rerun

        if submit_thread:
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

                # Save the thread
                save_message(name, message, message_tags, thread_visibility, True, thread_password, image_filename)
                st.success("Thread created successfully!")
                del st.session_state.creating_thread
                st.experimental_rerun()  # Rerun to refresh the state

# Load and display messages
st.markdown("### Messages")

messages = load_messages()  # Load messages again to ensure we're working with the latest version

# Check if a specific thread is selected
if 'selected_thread' in st.session_state:
    selected_thread = next((msg for msg in messages if msg['id'] == st.session_state['selected_thread']), None)
    if selected_thread:
        # Display only the selected thread's details
        st.markdown("### Thread Details")
        st.markdown(f"**{selected_thread['name']}** *({selected_thread['timestamp']})*")
        st.markdown(selected_thread['message'])
        if selected_thread.get('image'):
            st.image(os.path.join(IMAGES_DIR, selected_thread['image']), use_column_width=True)

        # Comments for the selected thread
        st.markdown("💬 Comments:")
        for comment in selected_thread.get('comments', []):
            st.markdown(f"**{comment['name']}**: {comment['comment']}")

        # Comment submission form for the selected thread
        with st.form(key=f'comment_form_{selected_thread["id"]}'):
            commenter_name = st.text_input("Your name:", key=f"commenter_name_{selected_thread['id']}")
            comment_text = st.text_area("Add a comment:", key=f"comment_text_{selected_thread['id']}")
            submit_comment = st.form_submit_button("Post Comment")
            
            if submit_comment:
                if not commenter_name.strip():
                    st.error("Please enter your name.")
                elif not comment_text.strip():
                    st.error("Please enter a comment.")
                else:
                    add_comment(selected_thread['id'], commenter_name, comment_text)
                    st.success("Comment added successfully!")
                    st.stop()  # Use stop() instead of rerun
        
        if st.button("Back to Messages"):
            del st.session_state.selected_thread  # Remove thread selection to go back
            st.experimental_rerun()  # Rerun to return to message view

else:
    # Apply filters and search
    filtered_messages = [
        msg for msg in messages 
        if (
            (search_query.lower() in msg['name'].lower() or search_query.lower() in msg['message'].lower() or any(tag.lower() in msg['tags'] for tag in selected_tags)) and 
            (visibility_filter == "All" or msg['visibility'] == visibility_filter.lower().replace(" only", ""))
        )
    ]

    if filtered_messages:
        for msg in filtered_messages:
            # Display each message with dividers
            st.markdown("---")
            st.markdown(f"**{msg['name']}** *({msg['timestamp']})*")
            st.markdown(msg['message'])
            if msg.get('image'):
                st.image(os.path.join(IMAGES_DIR, msg['image']), use_column_width=True)

            # Comment section
            st.markdown("💬 Comments:")
            for comment in msg.get('comments', []):
                st.markdown(f"**{comment['name']}**: {comment['comment']}")

            # Comment submission form
            with st.form(key=f'comment_form_{msg["id"]}'):
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
                        st.stop()  # Use stop() instead of rerun

        st.markdown("---")
    else:
        st.info("No messages yet. Be the first to leave a message!")

# Sidebar for threads
st.sidebar.header("Threads")
threads = [msg for msg in messages if msg.get('is_thread')]  # Only show threads in the sidebar

if threads:
    for thread in threads:
        st.sidebar.markdown(f"**{thread['name']}**")
        st.sidebar.markdown(f"*{thread['timestamp']}*")
        st.sidebar.markdown(f"> {thread['message'][:50]}...")  # Show a snippet of the thread message
        thread_link = st.sidebar.button("Open Thread", key=f"thread_{thread['id']}")
        
        if thread_link:
            # Set the selected thread in session state
            st.session_state.selected_thread = thread['id']
            # Use st.stop() instead of rerun
            st.stop()  # Stop execution to update the view
else:
    st.sidebar.info("No threads available.")
