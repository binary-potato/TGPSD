import streamlit as st
import json
import os
from datetime import datetime
import uuid
from PIL import Image
import hashlib

# Constants
MESSAGES_FILE = "messages.json"
SPACES_FILE = "spaces.json"
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

# New functions for chat spaces
def load_spaces():
    if os.path.exists(SPACES_FILE):
        with open(SPACES_FILE, "r") as f:
            return json.load(f)
    return {"public": [], "private": []}

def save_spaces(spaces):
    with open(SPACES_FILE, "w") as f:
        json.dump(spaces, f, indent=4)

def create_space(name, is_private, password=None):
    spaces = load_spaces()
    space_type = "private" if is_private else "public"
    new_space = {"name": name, "id": str(uuid.uuid4())}
    if is_private:
        new_space["password_hash"] = hashlib.sha256(password.encode()).hexdigest()
    spaces[space_type].append(new_space)
    save_spaces(spaces)

def verify_space_password(space_id, password):
    spaces = load_spaces()
    for space in spaces["private"]:
        if space["id"] == space_id:
            return space["password_hash"] == hashlib.sha256(password.encode()).hexdigest()
    return False

# Set page title and header with slogan
st.set_page_config(page_title="TGPSD", page_icon="📓", layout="wide")

# Sidebar
st.sidebar.title("TGPSD")

# Display existing spaces in the sidebar
spaces = load_spaces()
st.sidebar.header("Chat Spaces")
st.sidebar.subheader("Public Spaces")
for space in spaces["public"]:
    if st.sidebar.button(space["name"], key=f"public_{space['id']}"):
        st.experimental_set_query_params(space=space["id"])
        st.rerun()

st.sidebar.subheader("Private Spaces")
for space in spaces["private"]:
    if st.sidebar.button(space["name"], key=f"private_{space['id']}"):
        st.experimental_set_query_params(space=space["id"])
        st.rerun()

# Create new space form
with st.sidebar.expander("Create New Space"):
    with st.form(key="new_space_form"):
        space_name = st.text_input("Space Name")
        is_private = st.checkbox("Private Space")
        password = st.text_input("Password (for private spaces)", type="password") if is_private else None
        create_space_button = st.form_submit_button("Create Space")

        if create_space_button:
            if not space_name:
                st.error("Please enter a space name.")
            elif is_private and not password:
                st.error("Please enter a password for the private space.")
            else:
                create_space(space_name, is_private, password)
                st.success(f"Space '{space_name}' created successfully!")
                st.rerun()

# Search and Filter Section in sidebar with search icon
st.sidebar.header("🔍 Search and Filter")
search_query = st.sidebar.text_input("Search messages:", "", 
    placeholder="Search by name, message, or tags...")
selected_tags = st.sidebar.multiselect("Filter by tags:", TAGS)

# Main content
current_space_id = st.query_params.get("space", [None])[0]

if current_space_id:
    # Load the current space
    current_space = None
    for space_type in ["public", "private"]:
        for space in spaces[space_type]:
            if space["id"] == current_space_id:
                current_space = space
                break
        if current_space:
            break

    if current_space:
        st.title(f"Chat Space: {current_space['name']}")

        # Password protection for private spaces
        if "password_hash" in current_space:
            password = st.text_input("Enter password to access this space:", type="password")
            if not verify_space_password(current_space["id"], password):
                st.error("Incorrect password. Please try again.")
                st.stop()

        # Rest of the chat space functionality
        
        st.subheader("""
        For students who want to make a mark. Report identity at chuisaac2014b@gmail.com

        **How to use:**
        - You can format your message using **Markdown**. For example:
          - Use `**bold**` for bold text.
          - Use `*italic*` for italic text.
          - Use `-` for lists.
          - Emojis are supported too! 🎉
        - Add tags to categorize your message
        - Comment on messages to start discussions
        - Optionally, upload an image with your message (PNG, JPG, JPEG, GIF).
        """)

        # Message Submission Form inside an Accordion (Expander)
        with st.expander("Leave a Message"):
            with st.form(key='message_form'):
                st.markdown("### Enter your Message")
                name = st.text_input("Enter your name:", max_chars=50)
                message = st.text_area("Enter your message:", height=150)
                message_tags = st.multiselect("Select tags for your message:", TAGS)
                uploaded_image = st.file_uploader("Upload an image (optional):", type=["png", "jpg", "jpeg", "gif"])
                submit_button = st.form_submit_button(label='Submit')

        # Handle Form Submission
        if submit_button:
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
                st.rerun()

        # Add search status message when filtering
        messages = load_messages()
        if search_query or selected_tags:
            st.markdown("##### 🔍 Showing filtered results")

        # Display Filtered Messages
        st.markdown("### Messages")

        if messages:
            filtered_messages = messages
            
            # Apply search filter
            if search_query:
                search_query = search_query.lower()
                filtered_messages = [
                    msg for msg in filtered_messages
                    if search_query in msg['name'].lower() or 
                    search_query in msg['message'].lower() or 
                    any(search_query in tag.lower() for tag in msg.get('tags', []))
                ]
            
            # Apply tag filter
            if selected_tags:
                filtered_messages = [
                    msg for msg in filtered_messages
                    if any(tag in msg.get('tags', []) for tag in selected_tags)
                ]
            
            if not filtered_messages:
                st.info("🔍 No messages found matching your search criteria.")
            
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
        else:
            st.info("No messages yet. Be the first to leave a message!")

    else:
        st.error("Invalid space ID. Please select a valid space from the sidebar.")
else:
    # Original main page content
    # Upload the logo image
    

    st.title("TGPSD")
    st.subheader("""
    For students who want to make a mark. Report false identity at chuisaac2014b@gmail.com

    **How to use:**
    - You can format your message using **Markdown**. For example:
      - Use `**bold**` for bold text.
      - Use `*italic*` for italic text.
      - Use `-` for lists.
      - Emojis are supported too! 🎉
    - Add tags to categorize your message
    - Comment on messages to start discussions
    - Optionally, upload an image with your message (PNG, JPG, JPEG, GIF).
    """)

    # Message Submission Form inside an Accordion (Expander)
    with st.expander("Leave a Message"):
        with st.form(key='message_form'):
            st.markdown("### Enter your Message")
            name = st.text_input("Enter your name:", max_chars=50)
            message = st.text_area("Enter your message:", height=150)
            message_tags = st.multiselect("Select tags for your message:", TAGS)
            uploaded_image = st.file_uploader("Upload an image (optional):", type=["png", "jpg", "jpeg", "gif"])
            submit_button = st.form_submit_button(label='Submit')

    # Handle Form Submission
    if submit_button:
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
            st.rerun()

    # Add search status message when filtering
    messages = load_messages()
    if search_query or selected_tags:
        st.markdown("##### 🔍 Showing filtered results")

    # Display Filtered Messages
    st.markdown("### Messages")

    if messages:
        filtered_messages = messages
        
        # Apply search filter
        if search_query:
            search_query = search_query.lower()
            filtered_messages = [
                msg for msg in filtered_messages
                if search_query in msg['name'].lower() or 
                search_query in msg['message'].lower() or 
                any(search_query in tag.lower() for tag in msg.get('tags', []))
            ]
        
        # Apply tag filter
        if selected_tags:
            filtered_messages = [
                msg for msg in filtered_messages
                if any(tag in msg.get('tags', []) for tag in selected_tags)
            ]
        
        if not filtered_messages:
            st.info("🔍 No messages found matching your search criteria.")
        
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
    else:
        st.info("No messages yet. Be the first to leave a message!")