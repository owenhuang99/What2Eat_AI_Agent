"""
This file is the main file for the front end of the restaurant ordering helper.
"""
import os
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv('.env'))

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import sys
from pathlib import Path
import streamlit as st
import pandas as pd
import os
import asyncio
from datetime import datetime
import json
import base64
from PIL import Image
import io
import re
import time

from src.agent.agent import RestaurantAgent
from src.utils.data_utils import load_health_data
from src.utils.constants import HEALTH_REPORT_FORMAT, HEALTH_REPORT_TIPS, CHAT_INTERFACE_CSS, CHAT_HELP_TEXT
from src.ui.components.new_user import new_user_workflow
from src.ui.components.existing_user import existing_user_workflow
from src.ui.components.initialize import initialize_agent, initialize_session_state
from src.ui.components.display_info import display_health_info
from src.ui.components.health_tab import health_tab

# Set page config
st.set_page_config(
    page_title="Restaurant Ordering Helper",
    page_icon="🍽️",
    layout="wide"
)

# Custom CSS for chat interface
st.markdown(CHAT_INTERFACE_CSS, unsafe_allow_html=True)

def display_chat_message(message, is_user=False):
    """Display a chat message with appropriate styling"""
    message_class = "user-message" if is_user else "assistant-message"
    sender = "You" if is_user else "Assistant"
    
    # Extract content from message if it's a dictionary
    if isinstance(message, dict):
        message_content = message.get("content", "")
        
        if "images" in message and message["images"]:
            message_content += "<br>"
            for img_data in message["images"]:
                if "image_url" in img_data and img_data["image_url"]:
                    dish_name = img_data.get("dish_name", "Generated dish")
                    message_content += f'<img src="{img_data["image_url"]}" alt="{dish_name}" style="max-width: 300px; border-radius: 8px; margin: 10px 0;" /><br>'
                    message_content += f'<div style="text-align: center; margin-bottom: 15px;"><small>{dish_name}</small></div>'
    else:
        message_content = str(message)
    
    st.markdown(f"""
    <div class="{message_class}">
        <div class="message-sender">{sender}</div>
        <div class="message-content">{message_content}</div>
    </div>
    """, unsafe_allow_html=True)



def display_chat_history():
    """Display the chat history."""
    if "chat_history" in st.session_state:
        for message in st.session_state.chat_history:
            role = message.get("role", "")
            if role == "user":
                display_chat_message(message, is_user=True)
            else:  # assistant
                display_chat_message(message, is_user=False)

def home_tab():
    """Home tab implementation with chat interface and recommendations"""
    # Home Title
    st.markdown(
        f"""
        <div style="display: flex; justify-content: center; align-items: center;">
            <h1 style="font-size: 32px; margin: 0;">Order Agent</h1>
        </div>
        """,
        unsafe_allow_html=True)

    # agent state check
    # ensure agent is initialized
    if 'agent' not in st.session_state or st.session_state.agent is None:
        st.session_state.agent = RestaurantAgent(st.session_state.user_id)

    # ensure health data is added to agent
    if "health_data" not in st.session_state.agent.conversation_context:
        health_data = load_health_data()
        user_data = health_data[health_data['user_id'].astype(str) == str(st.session_state.user_id)]
        if not user_data.empty:
            health_data_dict = user_data.iloc[0].to_dict()
            health_data_dict = {k: v for k, v in health_data_dict.items() if pd.notna(v)}
            st.session_state.agent.conversation_context["health_data"] = health_data_dict

    # ensure budget data is added to agent
    if "budget" not in st.session_state.agent.conversation_context and st.session_state.budget is not None:
        st.session_state.agent.conversation_context["budget"] = {
            "min": st.session_state.budget[0],
            "max": st.session_state.budget[1]
        }

    # ensure food preference data is added to agent
    if "food_preference" not in st.session_state.agent.conversation_context and st.session_state.food_preference is not None:
        st.session_state.agent.conversation_context["food_preference"] = st.session_state.food_preference



    # Chat interface
    st.markdown("---")
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    display_chat_history()
    st.markdown('</div>', unsafe_allow_html=True)

    # TODO: Now this input box to the bottom of the page, move it to above the action buttons.
    # Chat input
    user_input = st.chat_input("Chat with AI Agent Here:", key="chat_input")

    if user_input:
        st.session_state.chat_history.append({
            'role': 'user',
            'content': user_input
        })

        with st.spinner("Processing..."):
            try:
                response = st.session_state.agent.process_input(user_input)
                if response.get('status') == 'success':
                    if 'screenshot' in response:
                        st.image(response['screenshot'], caption="Search Results")
                    if 'message' in response:
                        st.session_state.chat_history.append({
                            'role': 'assistant',
                            'content': response['message']
                        })
                    if 'recommendations' in response:
                        st.session_state.chat_history.append({
                            'role': 'assistant',
                            'content': response['recommendations']
                        })
                else:
                    st.session_state.chat_history.append({
                        'role': 'assistant',
                        'content': f"Error: {response.get('message', 'Unknown error')}"
                    })


            except Exception as e:
                st.error(f"Error processing input: {str(e)}")
                st.session_state.chat_history.append({
                    'role': 'assistant',
                    'content': f"Error: {str(e)}"
                })
        st.rerun()

    # Action buttons
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Get Dish Recommendations", key="get_recommendations_btn"):
            if st.session_state.agent:
                try:
                    # Check if restaurant is already selected
                    current_restaurant = st.session_state.agent.conversation_context.get("current_restaurant")
                    if not current_restaurant:
                        st.error("Please specify a restaurant first in the chat above.")
                    else:
                        # Set generate_images to False - we're just getting text recommendations
                        st.session_state.agent.conversation_context["generate_images"] = False
                        
                        # Add message to chat history
                        st.session_state.chat_history.append({
                            "role": "user", 
                            "content": f"Please recommend dishes for me based on my budget of ${st.session_state.budget[0]}-${st.session_state.budget[1]} and my food preferences."
                        })
                        
                        # Get recommendations from agent
                        with st.spinner("Getting recommendations..."):
                            # First check if we have menu items
                            if not st.session_state.agent.conversation_context.get("menu_items"):
                                st.info("Fetching menu first...")
                                menu_result = st.session_state.agent.handle_input(
                                    "get menu",
                                    force_action="get_menu"
                                )
                                if menu_result.get("status") != "success":
                                    st.error("Couldn't fetch menu. Please try again.")
                                    return


                            # Get recommendations using handle_input
                            response = st.session_state.agent.handle_input(
                                "recommend dishes",
                                force_action="recommendations"
                            )

                            
                        # Process and display the recommendations
                        if response and response.get("status") == "success":
                            st.session_state.chat_history.append({
                                'role': 'assistant',
                                'content': response.get("message", "No recommendations available.")
                            })
                        else:
                            error_msg = response.get("message", "Failed to get recommendations.")
                            st.session_state.chat_history.append({
                                'role': 'assistant',
                                'content': f"Error: {error_msg}"
                            })
                        st.rerun()
                except Exception as e:
                    st.error(f"Error getting recommendations: {str(e)}")
            else:
                st.error("Agent not initialized. Please reload the page.")
    
    with col2:
        if st.button("Generate Dish Pictures", key="generate_images_btn"):
            if st.session_state.agent:
                try:
                    # Check if restaurant is already selected
                    current_restaurant = st.session_state.agent.conversation_context.get("current_restaurant")
                    if not current_restaurant:
                        st.error("Please specify a restaurant first in the chat above.")
                    else:
                        # Step 1: generate text recommendations
                        st.session_state.agent.conversation_context["generate_images"] = False
                        recommend_response = st.session_state.agent.handle_input(
                            "recommend dishes",
                            force_action="recommendations"
                        )
                        if recommend_response.get("status") != "success":
                            st.error("Failed to generate dish recommendations. Cannot generate images.")
                            return
                        
                        # Step 2: generate images based on text recommendations
                        st.session_state.agent.conversation_context["generate_images"] = True
                        with st.spinner("Generating dish images... this may take a while"):
                            response = st.session_state.agent.handle_input(
                                "generate dish images",
                                force_action="recommendations"
                            )
                        
                        if response and response.get("status") == "success":
                            dish_images = response.get("dish_images", [])
                            if dish_images:
                                st.session_state.chat_history.append({
                                    "role": "assistant",
                                    "content": "Here are images for the recommended dishes:",
                                    "images": dish_images
                                })
                        else:
                            error_msg = response.get("message", "Failed to generate dish images.")
                            st.session_state.chat_history.append({
                                'role': 'assistant',
                                'content': f"Error: {error_msg}"
                            })
                        
                        # Turn off the flag after generation
                        st.session_state.agent.conversation_context["generate_images"] = False

                        st.rerun()
                except Exception as e:
                    st.error(f"Error generating dish images: {str(e)}")
            else:
                st.error("Agent not initialized. Please reload the page.")
    
    with col3:
        if st.button("Get Health Advice", key="health_advice_btn"):
            if st.session_state.agent:
                try:
                    st.session_state.chat_history.append({
                        "role": "user", 
                        "content": "Please provide some health advice based on my health profile and dietary preferences."
                    })
                    
                    with st.spinner("Getting health advice..."):
                        response = st.session_state.agent.handle_input(
                            "health advice",
                            force_action="health_query"
                        )
                    
                    if response and response.get("status") == "success":
                        st.session_state.chat_history.append({
                            'role': 'assistant',
                            'content': response.get("message", "Sorry, no health advice available.")
                        })
                    else:
                        error_msg = response.get("message", "Failed to get health advice.")
                        st.session_state.chat_history.append({
                            'role': 'assistant',
                            'content': f"Error: {error_msg}"
                        })

                    
                    st.rerun()
                except Exception as e:
                    st.error(f"Error getting health advice: {str(e)}")
            else:
                st.error("Agent not initialized. Please reload the page.")

    # Add help section under buttons
    with st.expander("Need help? Click here for examples"):
        st.markdown(CHAT_HELP_TEXT)

def main():
    """Main application entry point"""
    # Initialize session state
    initialize_session_state()

    # Initial page - User verification and registration
    if st.session_state.user_id is None:
        # Login Title
        st.markdown(
            "<h1 style='text-align: center;'>Restaurant Ordering Helper - Login</h1>",
            unsafe_allow_html=True
        )

        # New user check
        if st.session_state.is_new_user is None:
            col1, col2, col3 = st.columns([1, 2, 1])  # Wider middle for the content
            with col2:  # Put everything inside the center column
                st.markdown("---")

                # Create container for login and adjust size
                with st.container(border=True, height=300):
                    # Centered header
                    st.markdown("<p style='text-align: center; font-size: 16px;'>Are you a new user?</p>",
                                unsafe_allow_html=True)

                    # Stack Yes and No buttons vertically and centered
                    col_a, col_b, col_c = st.columns([1, 2, 1])  # To center buttons
                    with col_b:
                        if st.button("Yes"):
                            st.session_state.is_new_user = True
                            st.rerun()

                        if st.button("No"):
                            st.session_state.is_new_user = False
                            st.rerun()

            return

        # If new user, route to new user workflow
        if st.session_state.is_new_user:
            # Create container for login and adjust size
            with st.container(border=True):
                new_user_workflow()
        # If existing user, route to existing user workflow
        else:
            col1, col2, col3 = st.columns([1, 2, 1])  # Wider middle for the content
            with col2:  # Put everything inside the center column
                st.markdown("---")
                # Create container for login and adjust size
                with st.container(border=True, height=300):
                    existing_user_workflow()
    
    # Main application interface
    else:
        # If user_id is set but budget or food preference is not set, show the combined form
        if st.session_state.user_id is not None and (st.session_state.budget is None or st.session_state.food_preference is None):
            st.title(f"Welcome, User {st.session_state.user_id}")
            
            # Create a container for the combined form
            with st.container(border=True):
                st.markdown("<h3 style='text-align: center;'>Set Your Preferences</h3>", unsafe_allow_html=True)
                st.markdown("---")
                
                # Meal Time Selection
                st.markdown("### 🕒 Meal Time")
                meal_time = st.selectbox("What time of day is it?", ["Breakfast", "Lunch", "Dinner"])
                st.session_state.agent.conversation_context["meal_time"] = meal_time
                
                # Budget Section
                st.markdown("### 💵 Budget")
                st.markdown("Set your budget range for meal recommendations.")
                
                # Budget input with slider
                budget = st.slider(
                    "What is Your Budget Range?",
                    min_value=0,
                    max_value=1000,
                    value=(0, 1000),
                    step=10,
                    help="Adjust the slider to set your minimum and maximum budget"
                )
                
                # Create Vars for the min and max ranges of the selected range
                budget_min, budget_max = budget
                
                st.markdown("---")
                
                # Food Preferences Section
                st.markdown("### 🍽️ Food Preferences")
                st.markdown("Select your preferred food categories.")
                
                # Define food category options
                food_categories = ["No Preference", "Beef", "Chicken", "Pork", "Seafood", "Salad", "Soup", "Drink", "Dessert"]
                
                # Multi-select for food categories
                selected_categories = st.multiselect(
                    "Select food categories:", 
                    options=food_categories,
                    default=None,
                    help="Choose one or more food categories you prefer"
                )
                
                # Option for custom preference
                st.markdown("---")
                st.markdown("#### 🎯 Custom Preferences")
                custom_preference = None
                if st.checkbox("Other (specify your own preference)", key="custom_food_pref_checkbox"):
                    custom_preference = st.text_input(
                        "Enter your food preference:", 
                        key="custom_food_pref_input",
                        help="Example: Korean BBQ, Sushi, Pizza, etc."
                    )
                
                # Submit button at the bottom
                if st.button("Save Preferences", key="save_preferences"):
                    # Validate budget
                    if budget_min == 0 and budget_max == 1000:
                        st.warning("Please adjust the budget range to something more specific")
                    else:
                        # Save budget
                        st.session_state.budget = (budget_min, budget_max)
                        
                        # Save food preferences
                        preferences = []
                        if selected_categories:
                            preferences.extend(selected_categories)
                        if custom_preference:
                            preferences.append(custom_preference)
                        
                        if not preferences:
                            # Default to No Preference if nothing selected
                            preferences = ["No Preference"]
                        
                        # Store as comma-separated string
                        preference_str = ", ".join(preferences)
                        st.session_state.food_preference = preference_str
                        
                        # Initialize agent if needed
                        agent_initialized = initialize_agent()
                        if agent_initialized and st.session_state.agent is not None:
                            # Add budget to agent conversation_context
                            st.session_state.agent.conversation_context["budget"] = {
                                "min": budget_min,
                                "max": budget_max
                            }
                            # Add preferences to agent conversation context
                            st.session_state.agent.conversation_context["food_preference"] = preference_str
                            st.success("Preferences saved successfully!")
                            st.rerun()
                        else:
                            st.error("Failed to initialize agent. Please try again.")

        # Main application interface with navigation
        else:
            # Navigation on Side bar
            st.sidebar.write(f"Welcome, {st.session_state.user_id}")
            st.sidebar.write(f" ")
            selected = st.sidebar.radio("Navigate:", [
                "🏠 Home",
                "💪 Health & Preferences"
            ])

            # Home Tab
            if "Home" in selected:
                home_tab()

            # Health Tab
            elif "Health" in selected:
                health_tab()

if __name__ == "__main__":
    # Create a new event loop for Streamlit
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    main()
