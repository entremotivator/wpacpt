import streamlit as st
import requests
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from requests.auth import HTTPBasicAuth
import base64
from datetime import datetime, timedelta
import time
import re
import io
from PIL import Image

# Set page configuration
st.set_page_config(
    page_title="WordPress ACPT Manager Pro",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E88E5;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #424242;
        margin-bottom: 1rem;
    }
    .card {
        padding: 1.5rem;
        border-radius: 0.5rem;
        background-color: #f8f9fa;
        margin-bottom: 1rem;
        border-left: 4px solid #1E88E5;
    }
    .success-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #e3f2fd;
        margin-bottom: 1rem;
        border-left: 4px solid #4CAF50;
    }
    .warning-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #fff8e1;
        margin-bottom: 1rem;
        border-left: 4px solid #FFC107;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
    }
    .stTabs [data-baseweb="tab"] {
        height: 4rem;
        white-space: pre-wrap;
        background-color: white;
        border-radius: 4px 4px 0px 0px;
        gap: 1rem;
        padding-top: 0.5rem;
        padding-bottom: 0.5rem;
    }
    .stTabs [aria-selected="true"] {
        background-color: #e3f2fd;
        border-bottom: 4px solid #1E88E5;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state for storing data between reruns
if 'posts' not in st.session_state:
    st.session_state.posts = []
if 'templates' not in st.session_state:
    st.session_state.templates = {}
if 'current_template' not in st.session_state:
    st.session_state.current_template = None
if 'auth_token' not in st.session_state:
    st.session_state.auth_token = None
if 'connection_status' not in st.session_state:
    st.session_state.connection_status = False

# App header
st.markdown('<p class="main-header">WordPress ACPT Manager Pro</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Comprehensive Custom Post Type Management with Industry Templates</p>', unsafe_allow_html=True)

# Sidebar for WordPress connection settings
with st.sidebar:
    st.header("Connection Settings")
    
    # Connection settings
    wp_url = st.text_input("WordPress URL", placeholder="https://example.com")
    
    auth_method = st.radio("Authentication Method", ["None", "Basic Auth", "Application Password", "JWT/OAuth"])
    
    username = ""
    password = ""
    token = ""
    
    if auth_method == "JWT/OAuth":
        token = st.text_input("Authentication Token", type="password")
        st.session_state.auth_token = token
    elif auth_method in ["Basic Auth", "Application Password"]:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
    
    # Test connection button
    if st.button("Test Connection"):
        if not wp_url:
            st.error("Please enter a WordPress URL")
        else:
            with st.spinner("Testing connection..."):
                try:
                    endpoint = f"{wp_url.rstrip('/')}/wp-json/"
                    
                    headers = {"Content-Type": "application/json"}
                    auth = None
                    
                    if auth_method == "JWT/OAuth" and token:
                        headers["Authorization"] = f"Bearer {token}"
                    elif auth_method in ["Basic Auth", "Application Password"] and username and password:
                        auth = HTTPBasicAuth(username, password)
                    
                    response = requests.get(endpoint, headers=headers, auth=auth, timeout=10)
                    
                    if response.status_code == 200:
                        st.success("Connection successful!")
                        st.session_state.connection_status = True
                    else:
                        st.error(f"Connection failed: {response.status_code} - {response.reason}")
                        st.session_state.connection_status = False
                except Exception as e:
                    st.error(f"Connection error: {str(e)}")
                    st.session_state.connection_status = False
    
    st.divider()
    
    # Post type selection
    st.header("Post Type")
    post_type = st.selectbox("Select Post Type", ["post", "product", "page", "property", "stock", "assessment", "custom"])
    
    if post_type == "custom":
        post_type = st.text_input("Enter Custom Post Type")
    
    # Template selection
    st.header("Industry Templates")
    template_category = st.selectbox("Select Template Category", 
                                    ["None", "Real Estate", "Stock Market", "DISC Assessment", "Product Catalog", "Event Management"])
    
    if template_category != "None":
        if template_category == "Real Estate":
            template_name = st.selectbox("Select Template", 
                                        ["Residential Property", "Commercial Property", "Rental Listing", "Land Listing"])
        elif template_category == "Stock Market":
            template_name = st.selectbox("Select Template", 
                                        ["Stock Profile", "Market Analysis", "Portfolio Summary", "Financial Report"])
        elif template_category == "DISC Assessment":
            template_name = st.selectbox("Select Template", 
                                        ["Individual Assessment", "Team Assessment", "Leadership Profile", "Career Recommendation"])
        elif template_category == "Product Catalog":
            template_name = st.selectbox("Select Template", 
                                        ["Physical Product", "Digital Product", "Service Offering", "Subscription"])
        elif template_category == "Event Management":
            template_name = st.selectbox("Select Template", 
                                        ["Conference", "Workshop", "Webinar", "Social Event"])
        
        if st.button("Load Template"):
            st.session_state.current_template = f"{template_category} - {template_name}"
            st.success(f"Template loaded: {template_name}")
    
    st.divider()
    
    # Help section
    with st.expander("Help & Documentation"):
        st.markdown("""
        ### Quick Start Guide
        
        1. Enter your WordPress site URL
        2. Select authentication method and enter credentials
        3. Test the connection
        4. Choose a post type and template
        5. Use the tabs to view, create, or export posts
        
        ### About ACPT
        
        Advanced Custom Post Types (ACPT) is a WordPress plugin that allows you to create and manage custom post types and meta fields through a user-friendly interface.
        
        This app helps you interact with ACPT through the WordPress REST API.
        
        [Visit ACPT Documentation](https://acpt.io/documentation/)
        """)

# Functions for API interaction
def get_posts(wp_url, post_type, username=None, password=None, token=None, params=None):
    endpoint = f"{wp_url.rstrip('/')}/wp-json/wp/v2/{post_type}"
    
    headers = {
        "Content-Type": "application/json"
    }
    
    auth = None
    if token:
        headers["Authorization"] = f"Bearer {token}"
    elif username and password:
        auth = HTTPBasicAuth(username, password)
    
    try:
        response = requests.get(endpoint, headers=headers, auth=auth, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching posts: {str(e)}")
        if hasattr(e, 'response') and e.response:
            st.error(f"Response: {e.response.text}")
        return []

def create_post(wp_url, post_type, post_data, username=None, password=None, token=None):
    endpoint = f"{wp_url.rstrip('/')}/wp-json/wp/v2/{post_type}"
    
    headers = {
        "Content-Type": "application/json"
    }
    
    auth = None
    if token:
        headers["Authorization"] = f"Bearer {token}"
    elif username and password:
        auth = HTTPBasicAuth(username, password)
    
    try:
        response = requests.post(endpoint, headers=headers, auth=auth, json=post_data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error creating post: {str(e)}")
        if hasattr(e, 'response') and e.response:
            st.error(f"Response: {e.response.text}")
        return None

def update_post(wp_url, post_type, post_id, post_data, username=None, password=None, token=None):
    endpoint = f"{wp_url.rstrip('/')}/wp-json/wp/v2/{post_type}/{post_id}"
    
    headers = {
        "Content-Type": "application/json"
    }
    
    auth = None
    if token:
        headers["Authorization"] = f"Bearer {token}"
    elif username and password:
        auth = HTTPBasicAuth(username, password)
    
    try:
        response = requests.put(endpoint, headers=headers, auth=auth, json=post_data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error updating post: {str(e)}")
        if hasattr(e, 'response') and e.response:
            st.error(f"Response: {e.response.text}")
        return None

def delete_post(wp_url, post_type, post_id, username=None, password=None, token=None):
    endpoint = f"{wp_url.rstrip('/')}/wp-json/wp/v2/{post_type}/{post_id}?force=true"
    
    headers = {
        "Content-Type": "application/json"
    }
    
    auth = None
    if token:
        headers["Authorization"] = f"Bearer {token}"
    elif username and password:
        auth = HTTPBasicAuth(username, password)
    
    try:
        response = requests.delete(endpoint, headers=headers, auth=auth)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error deleting post: {str(e)}")
        if hasattr(e, 'response') and e.response:
            st.error(f"Response: {e.response.text}")
        return None

# Function to get template data
def get_template_data(template_name):
    # Real Estate Templates
    if template_name == "Real Estate - Residential Property":
        return {
            "title": "Sample Residential Property",
            "content": "<p>Beautiful residential property in a prime location.</p>",
            "status": "draft",
            "acpt": {
                "meta": [
                    {
                        "box": "property_details",
                        "field": "property_type",
                        "value": "Residential"
                    },
                    {
                        "box": "property_details",
                        "field": "bedrooms",
                        "value": 3
                    },
                    {
                        "box": "property_details",
                        "field": "bathrooms",
                        "value": 2
                    },
                    {
                        "box": "property_details",
                        "field": "square_feet",
                        "value": 2000
                    },
                    {
                        "box": "property_details",
                        "field": "year_built",
                        "value": 2010
                    },
                    {
                        "box": "location",
                        "field": "address",
                        "value": "123 Main Street"
                    },
                    {
                        "box": "location",
                        "field": "city",
                        "value": "Anytown"
                    },
                    {
                        "box": "location",
                        "field": "state",
                        "value": "CA"
                    },
                    {
                        "box": "location",
                        "field": "zip_code",
                        "value": "90210"
                    },
                    {
                        "box": "location",
                        "field": "country",
                        "value": "USA"
                    },
                    {
                        "box": "pricing",
                        "field": "price",
                        "value": 450000
                    },
                    {
                        "box": "pricing",
                        "field": "price_per_sqft",
                        "value": 225
                    },
                    {
                        "box": "features",
                        "field": "amenities",
                        "value": ["Garage", "Swimming Pool", "Garden", "Fireplace"]
                    },
                    {
                        "box": "features",
                        "field": "heating_cooling",
                        "value": "Central Air"
                    },
                    {
                        "box": "features",
                        "field": "parking",
                        "value": "2-Car Garage"
                    },
                    {
                        "box": "media",
                        "field": "featured_image",
                        "value": "https://example.com/property-image.jpg"
                    },
                    {
                        "box": "media",
                        "field": "virtual_tour",
                        "value": "https://example.com/virtual-tour"
                    }
                ]
            }
        }
    
    elif template_name == "Real Estate - Commercial Property":
        return {
            "title": "Sample Commercial Property",
            "content": "<p>Prime commercial property for your business needs.</p>",
            "status": "draft",
            "acpt": {
                "meta": [
                    {
                        "box": "property_details",
                        "field": "property_type",
                        "value": "Commercial"
                    },
                    {
                        "box": "property_details",
                        "field": "building_type",
                        "value": "Office"
                    },
                    {
                        "box": "property_details",
                        "field": "square_feet",
                        "value": 5000
                    },
                    {
                        "box": "property_details",
                        "field": "year_built",
                        "value": 2005
                    },
                    {
                        "box": "property_details",
                        "field": "floors",
                        "value": 2
                    },
                    {
                        "box": "location",
                        "field": "address",
                        "value": "456 Business Ave"
                    },
                    {
                        "box": "location",
                        "field": "city",
                        "value": "Metropolis"
                    },
                    {
                        "box": "location",
                        "field": "state",
                        "value": "NY"
                    },
                    {
                        "box": "location",
                        "field": "zip_code",
                        "value": "10001"
                    },
                    {
                        "box": "location",
                        "field": "country",
                        "value": "USA"
                    },
                    {
                        "box": "pricing",
                        "field": "price",
                        "value": 1200000
                    },
                    {
                        "box": "pricing",
                        "field": "price_per_sqft",
                        "value": 240
                    },
                    {
                        "box": "pricing",
                        "field": "lease_option",
                        "value": "Available"
                    },
                    {
                        "box": "pricing",
                        "field": "lease_rate",
                        "value": "25 per sqft/year"
                    },
                    {
                        "box": "features",
                        "field": "amenities",
                        "value": ["Elevator", "Conference Room", "Kitchen", "Security System"]
                    },
                    {
                        "box": "features",
                        "field": "parking",
                        "value": "20 Spaces"
                    },
                    {
                        "box": "features",
                        "field": "zoning",
                        "value": "Commercial"
                    },
                    {
                        "box": "media",
                        "field": "featured_image",
                        "value": "https://example.com/commercial-property.jpg"
                    },
                    {
                        "box": "media",
                        "field": "floor_plan",
                        "value": "https://example.com/floor-plan.pdf"
                    }
                ]
            }
        }
    
    # Stock Market Templates
    elif template_name == "Stock Market - Stock Profile":
        return {
            "title": "AAPL - Apple Inc.",
            "content": "<p>Apple Inc. designs, manufactures, and markets smartphones, personal computers, tablets, wearables, and accessories worldwide.</p>",
            "status": "draft",
            "acpt": {
                "meta": [
                    {
                        "box": "stock_info",
                        "field": "ticker",
                        "value": "AAPL"
                    },
                    {
                        "box": "stock_info",
                        "field": "company_name",
                        "value": "Apple Inc."
                    },
                    {
                        "box": "stock_info",
                        "field": "exchange",
                        "value": "NASDAQ"
                    },
                    {
                        "box": "stock_info",
                        "field": "sector",
                        "value": "Technology"
                    },
                    {
                        "box": "stock_info",
                        "field": "industry",
                        "value": "Consumer Electronics"
                    },
                    {
                        "box": "financials",
                        "field": "current_price",
                        "value": 175.43
                    },
                    {
                        "box": "financials",
                        "field": "market_cap",
                        "value": "2.85T"
                    },
                    {
                        "box": "financials",
                        "field": "pe_ratio",
                        "value": 28.76
                    },
                    {
                        "box": "financials",
                        "field": "dividend_yield",
                        "value": 0.55
                    },
                    {
                        "box": "financials",
                        "field": "52_week_high",
                        "value": 198.23
                    },
                    {
                        "box": "financials",
                        "field": "52_week_low",
                        "value": 124.17
                    },
                    {
                        "box": "performance",
                        "field": "daily_change",
                        "value": 1.25
                    },
                    {
                        "box": "performance",
                        "field": "ytd_return",
                        "value": 34.8
                    },
                    {
                        "box": "performance",
                        "field": "one_year_return",
                        "value": 42.5
                    },
                    {
                        "box": "performance",
                        "field": "five_year_return",
                        "value": 325.7
                    },
                    {
                        "box": "analysis",
                        "field": "analyst_rating",
                        "value": "Buy"
                    },
                    {
                        "box": "analysis",
                        "field": "price_target",
                        "value": 205.00
                    },
                    {
                        "box": "analysis",
                        "field": "analyst_consensus",
                        "value": ["Buy", "Buy", "Hold", "Buy", "Strong Buy"]
                    },
                    {
                        "box": "media",
                        "field": "company_logo",
                        "value": "https://example.com/apple-logo.png"
                    },
                    {
                        "box": "media",
                        "field": "price_chart",
                        "value": "https://example.com/aapl-chart.png"
                    }
                ]
            }
        }
    
    elif template_name == "Stock Market - Market Analysis":
        return {
            "title": "Market Analysis - Q2 2023",
            "content": "<p>Comprehensive analysis of market trends and sector performance for Q2 2023.</p>",
            "status": "draft",
            "acpt": {
                "meta": [
                    {
                        "box": "analysis_info",
                        "field": "period",
                        "value": "Q2 2023"
                    },
                    {
                        "box": "analysis_info",
                        "field": "analyst",
                        "value": "Jane Smith"
                    },
                    {
                        "box": "analysis_info",
                        "field": "publication_date",
                        "value": "2023-07-15"
                    },
                    {
                        "box": "market_overview",
                        "field": "sp500_performance",
                        "value": 8.3
                    },
                    {
                        "box": "market_overview",
                        "field": "nasdaq_performance",
                        "value": 12.5
                    },
                    {
                        "box": "market_overview",
                        "field": "dow_performance",
                        "value": 5.2
                    },
                    {
                        "box": "market_overview",
                        "field": "vix_average",
                        "value": 18.7
                    },
                    {
                        "box": "sector_performance",
                        "field": "technology",
                        "value": 15.3
                    },
                    {
                        "box": "sector_performance",
                        "field": "healthcare",
                        "value": 7.8
                    },
                    {
                        "box": "sector_performance",
                        "field": "financials",
                        "value": 4.2
                    },
                    {
                        "box": "sector_performance",
                        "field": "energy",
                        "value": -2.5
                    },
                    {
                        "box": "sector_performance",
                        "field": "consumer_discretionary",
                        "value": 9.7
                    },
                    {
                        "box": "sector_performance",
                        "field": "consumer_staples",
                        "value": 3.1
                    },
                    {
                        "box": "economic_indicators",
                        "field": "gdp_growth",
                        "value": 2.4
                    },
                    {
                        "box": "economic_indicators",
                        "field": "inflation_rate",
                        "value": 3.1
                    },
                    {
                        "box": "economic_indicators",
                        "field": "unemployment_rate",
                        "value": 3.6
                    },
                    {
                        "box": "economic_indicators",
                        "field": "fed_rate",
                        "value": 5.25
                    },
                    {
                        "box": "outlook",
                        "field": "market_outlook",
                        "value": "Cautiously Optimistic"
                    },
                    {
                        "box": "outlook",
                        "field": "recommended_sectors",
                        "value": ["Technology", "Healthcare", "Consumer Discretionary"]
                    },
                    {
                        "box": "outlook",
                        "field": "risk_factors",
                        "value": ["Inflation", "Geopolitical Tensions", "Supply Chain Disruptions"]
                    },
                    {
                        "box": "media",
                        "field": "market_chart",
                        "value": "https://example.com/market-q2-2023.png"
                    },
                    {
                        "box": "media",
                        "field": "sector_comparison_chart",
                        "value": "https://example.com/sector-comparison-q2-2023.png"
                    }
                ]
            }
        }
    
    # DISC Assessment Templates
    elif template_name == "DISC Assessment - Individual Assessment":
        return {
            "title": "DISC Assessment - John Doe",
            "content": "<p>DISC personality assessment results for John Doe.</p>",
            "status": "draft",
            "acpt": {
                "meta": [
                    {
                        "box": "assessment_info",
                        "field": "client_name",
                        "value": "John Doe"
                    },
                    {
                        "box": "assessment_info",
                        "field": "assessment_date",
                        "value": "2023-06-10"
                    },
                    {
                        "box": "assessment_info",
                        "field": "assessor",
                        "value": "Dr. Emily Johnson"
                    },
                    {
                        "box": "disc_scores",
                        "field": "dominance",
                        "value": 68
                    },
                    {
                        "box": "disc_scores",
                        "field": "influence",
                        "value": 82
                    },
                    {
                        "box": "disc_scores",
                        "field": "steadiness",
                        "value": 45
                    },
                    {
                        "box": "disc_scores",
                        "field": "conscientiousness",
                        "value": 73
                    },
                    {
                        "box": "personality_profile",
                        "field": "primary_style",
                        "value": "Influence"
                    },
                    {
                        "box": "personality_profile",
                        "field": "secondary_style",
                        "value": "Conscientiousness"
                    },
                    {
                        "box": "personality_profile",
                        "field": "behavioral_pattern",
                        "value": "Persuader"
                    },
                    {
                        "box": "personality_profile",
                        "field": "key_strengths",
                        "value": ["Enthusiastic", "Persuasive", "Organized", "Detail-oriented"]
                    },
                    {
                        "box": "personality_profile",
                        "field": "potential_limitations",
                        "value": ["May be overly talkative", "Can be impatient with routine tasks"]
                    },
                    {
                        "box": "work_style",
                        "field": "communication_style",
                        "value": "Open and expressive, but also values accuracy and precision"
                    },
                    {
                        "box": "work_style",
                        "field": "decision_making",
                        "value": "Makes decisions based on both people impact and logical analysis"
                    },
                    {
                        "box": "work_style",
                        "field": "team_role",
                        "value": "Motivator and Quality Controller"
                    },
                    {
                        "box": "work_style",
                        "field": "ideal_environment",
                        "value": "Collaborative setting with clear guidelines and opportunities to influence others"
                    },
                    {
                        "box": "recommendations",
                        "field": "development_areas",
                        "value": ["Active listening", "Patience with routine tasks", "Time management"]
                    },
                    {
                        "box": "recommendations",
                        "field": "career_matches",
                        "value": ["Sales Manager", "Marketing Director", "Project Manager", "Training Specialist"]
                    },
                    {
                        "box": "media",
                        "field": "disc_chart",
                        "value": "https://example.com/disc-chart-john-doe.png"
                    }
                ]
            }
        }
    
    elif template_name == "DISC Assessment - Team Assessment":
        return {
            "title": "Marketing Team DISC Assessment",
            "content": "<p>Comprehensive DISC assessment for the Marketing Team.</p>",
            "status": "draft",
            "acpt": {
                "meta": [
                    {
                        "box": "assessment_info",
                        "field": "team_name",
                        "value": "Marketing Team"
                    },
                    {
                        "box": "assessment_info",
                        "field": "department",
                        "value": "Marketing"
                    },
                    {
                        "box": "assessment_info",
                        "field": "assessment_date",
                        "value": "2023-05-15"
                    },
                    {
                        "box": "assessment_info",
                        "field": "team_size",
                        "value": 8
                    },
                    {
                        "box": "assessment_info",
                        "field": "assessor",
                        "value": "Dr. Robert Williams"
                    },
                    {
                        "box": "team_composition",
                        "field": "dominance_percentage",
                        "value": 25
                    },
                    {
                        "box": "team_composition",
                        "field": "influence_percentage",
                        "value": 38
                    },
                    {
                        "box": "team_composition",
                        "field": "steadiness_percentage",
                        "value": 12
                    },
                    {
                        "box": "team_composition",
                        "field": "conscientiousness_percentage",
                        "value": 25
                    },
                    {
                        "box": "team_composition",
                        "field": "primary_team_style",
                        "value": "Influence"
                    },
                    {
                        "box": "team_dynamics",
                        "field": "team_strengths",
                        "value": ["Creative problem-solving", "Persuasive communication", "Attention to detail", "Goal-oriented"]
                    },
                    {
                        "box": "team_dynamics",
                        "field": "team_challenges",
                        "value": ["May lack patience for implementation", "Could benefit from more process orientation", "Potential for conflict between task-focused and people-focused members"]
                    },
                    {
                        "box": "team_dynamics",
                        "field": "communication_patterns",
                        "value": "Primarily open and expressive, with some members preferring direct and factual communication"
                    },
                    {
                        "box": "team_dynamics",
                        "field": "decision_making_process",
                        "value": "Tends to be collaborative but can sometimes move too quickly without thorough analysis"
                    },
                    {
                        "box": "team_dynamics",
                        "field": "conflict_resolution_style",
                        "value": "Generally addresses conflicts openly, though some team members may avoid confrontation"
                    },
                    {
                        "box": "recommendations",
                        "field": "team_development",
                        "value": ["Implement structured project management processes", "Create clear roles that leverage individual DISC styles", "Establish communication protocols that respect different styles"]
                    },
                    {
                        "box": "recommendations",
                        "field": "leadership_approach",
                        "value": "Balance between providing clear direction and allowing creative freedom; recognize individual contributions"
                    },
                    {
                        "box": "recommendations",
                        "field": "team_building_activities",
                        "value": ["Problem-solving workshops", "Communication style training", "Role clarity exercises"]
                    },
                    {
                        "box": "media",
                        "field": "team_disc_chart",
                        "value": "https://example.com/marketing-team-disc.png"
                    },
                    {
                        "box": "media",
                        "field": "team_dynamics_chart",
                        "value": "https://example.com/team-dynamics-chart.png"
                    }
                ]
            }
        }
    
    # Default empty template
    return {
        "title": "",
        "content": "",
        "status": "draft",
        "acpt": {
            "meta": []
        }
    }

# Function to generate sample data for visualizations
def generate_sample_data(template_name):
    if "Real Estate" in template_name:
        # Generate sample property price data
        dates = pd.date_range(start='1/1/2023', periods=12, freq='M')
        prices = [450000, 455000, 460000, 458000, 465000, 470000, 475000, 480000, 485000, 490000, 495000, 500000]
        comparable_prices = [440000, 445000, 450000, 455000, 460000, 465000, 470000, 475000, 480000, 485000, 490000, 495000]
        
        price_df = pd.DataFrame({
            'Date': dates,
            'Property Price': prices,
            'Neighborhood Average': comparable_prices
        })
        
        # Generate sample property features data
        features = ['Bedrooms', 'Bathrooms', 'Square Feet', 'Garage Spaces', 'Age (Years)']
        property_values = [4, 3, 2500, 2, 5]
        comparable_values = [3, 2, 2200, 2, 8]
        
        features_df = pd.DataFrame({
            'Feature': features,
            'This Property': property_values,
            'Comparable Properties': comparable_values
        })
        
        return {
            'price_data': price_df,
            'features_data': features_df
        }
    
    elif "Stock Market" in template_name:
        # Generate sample stock price data
        dates = pd.date_range(start='1/1/2023', periods=30, freq='D')
        stock_prices = [150 + i + np.random.normal(0, 3) for i in range(30)]
        volume = [np.random.randint(5000000, 15000000) for _ in range(30)]
        
        stock_df = pd.DataFrame({
            'Date': dates,
            'Price': stock_prices,
            'Volume': volume
        })
        
        # Generate sample sector performance data
        sectors = ['Technology', 'Healthcare', 'Financials', 'Consumer Discretionary', 'Energy', 'Utilities', 'Materials']
        performance = [12.5, 8.3, 5.7, 9.2, -3.1, 2.8, 4.5]
        
        sector_df = pd.DataFrame({
            'Sector': sectors,
            'Performance (%)': performance
        })
        
        return {
            'stock_data': stock_df,
            'sector_data': sector_df
        }
    
    elif "DISC Assessment" in template_name:
        # Generate sample DISC scores
        categories = ['Dominance', 'Influence', 'Steadiness', 'Conscientiousness']
        individual_scores = [68, 82, 45, 73]
        team_average = [60, 65, 55, 62]
        
        disc_df = pd.DataFrame({
            'Category': categories,
            'Individual Score': individual_scores,
            'Team Average': team_average
        })
        
        # Generate sample behavioral traits data
        traits = ['Communication', 'Decision Making', 'Conflict Resolution', 'Problem Solving', 'Team Collaboration']
        scores = [85, 75, 60, 80, 90]
        
        traits_df = pd.DataFrame({
            'Trait': traits,
            'Score': scores
        })
        
        return {
            'disc_data': disc_df,
            'traits_data': traits_df
        }
    
    # Default empty data
    return {}

# Function to create visualizations based on template
def create_visualizations(template_name, data):
    if "Real Estate" in template_name and 'price_data' in data and 'features_data' in data:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Property Price Trend")
            fig = px.line(data['price_data'], x='Date', y=['Property Price', 'Neighborhood Average'],
                         title="Property Price vs. Neighborhood Average")
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("Property Features Comparison")
            fig = px.bar(data['features_data'], x='Feature', y=['This Property', 'Comparable Properties'],
                        barmode='group', title="Property Features Comparison")
            st.plotly_chart(fig, use_container_width=True)
        
        # Map visualization
        st.subheader("Property Location")
        st.markdown("*Map visualization would be displayed here with actual property coordinates*")
        
        # Placeholder for map
        st.image("https://via.placeholder.com/800x400?text=Property+Location+Map", use_column_width=True)
    
    elif "Stock Market" in template_name and 'stock_data' in data and 'sector_data' in data:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Stock Price History")
            fig = px.line(data['stock_data'], x='Date', y='Price', title="Stock Price History")
            
            # Add volume as bar chart on secondary y-axis
            fig2 = px.bar(data['stock_data'], x='Date', y='Volume', title="Trading Volume")
            fig.add_trace(go.Bar(x=data['stock_data']['Date'], y=data['stock_data']['Volume'], 
                                name='Volume', yaxis='y2', opacity=0.3))
            
            # Set up secondary y-axis
            fig.update_layout(
                yaxis2=dict(
                    title="Volume",
                    overlaying="y",
                    side="right"
                )
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("Sector Performance")
            fig = px.bar(data['sector_data'], x='Sector', y='Performance (%)', 
                        title="Sector Performance (%)", color='Performance (%)')
            st.plotly_chart(fig, use_container_width=True)
        
        # Additional visualization
        st.subheader("Price Movement Distribution")
        
        # Calculate daily returns
        data['stock_data']['Daily Return'] = data['stock_data']['Price'].pct_change() * 100
        
        fig = px.histogram(data['stock_data'].dropna(), x='Daily Return', 
                          title="Distribution of Daily Returns (%)",
                          nbins=20, histnorm='probability density')
        fig.add_vline(x=0, line_width=2, line_dash="dash", line_color="red")
        st.plotly_chart(fig, use_container_width=True)
    
    elif "DISC Assessment" in template_name and 'disc_data' in data and 'traits_data' in data:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("DISC Profile")
            fig = px.bar(data['disc_data'], x='Category', y=['Individual Score', 'Team Average'],
                        barmode='group', title="DISC Profile Comparison")
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("Behavioral Traits")
            fig = px.bar(data['traits_data'], x='Trait', y='Score', 
                        title="Behavioral Traits Assessment", color='Score',
                        color_continuous_scale=px.colors.sequential.Viridis)
            fig.update_layout(yaxis_range=[0, 100])
            st.plotly_chart(fig, use_container_width=True)
        
        # Radar chart for DISC profile
        st.subheader("DISC Profile Radar")
        
        fig = go.Figure()
        
        categories = data['disc_data']['Category'].tolist()
        categories.append(categories[0])  # Close the loop
        
        individual_scores = data['disc_data']['Individual Score'].tolist()
        individual_scores.append(individual_scores[0])  # Close the loop
        
        team_average = data['disc_data']['Team Average'].tolist()
        team_average.append(team_average[0])  # Close the loop
        
        fig.add_trace(go.Scatterpolar(
            r=individual_scores,
            theta=categories,
            fill='toself',
            name='Individual'
        ))
        
        fig.add_trace(go.Scatterpolar(
            r=team_average,
            theta=categories,
            fill='toself',
            name='Team Average'
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100]
                )
            ),
            showlegend=True
        )
        
        st.plotly_chart(fig, use_container_width=True)

# Main content area with tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📋 View Posts", 
    "➕ Create Post", 
    "📊 Visualize Data", 
    "📤 Export/Import", 
    "⚙️ Batch Operations"
])

# Tab 1: View Posts
with tab1:
    st.markdown('<p class="sub-header">View and Manage Posts</p>', unsafe_allow_html=True)
    
    # Search and filter options
    col1, col2, col3 = st.columns(3)
    
    with col1:
        search_term = st.text_input("Search by Title", placeholder="Enter keywords...")
    
    with col2:
        status_filter = st.selectbox("Filter by Status", ["All", "Published", "Draft", "Pending", "Private"])
    
    with col3:
        sort_by = st.selectbox("Sort by", ["Date (Newest)", "Date (Oldest)", "Title (A-Z)", "Title (Z-A)"])
    
    # Fetch posts button
    fetch_col1, fetch_col2 = st.columns([3, 1])
    
    with fetch_col1:
        if st.button("Fetch Posts", key="fetch_posts_tab1", use_container_width=True):
            if not wp_url:
                st.warning("Please enter a WordPress URL")
            else:
                with st.spinner("Fetching posts..."):
                    # Prepare parameters
                    params = {
                        "per_page": 100  # Fetch up to 100 posts
                    }
                    
                    if search_term:
                        params["search"] = search_term
                    
                    if status_filter != "All":
                        params["status"] = status_filter.lower()
                    
                    # Get authentication details
                    auth_token = st.session_state.auth_token if auth_method == "JWT/OAuth" else None
                    
                    # Fetch posts
                    posts = get_posts(wp_url, post_type, username, password, auth_token, params)
                    
                    if posts:
                        st.session_state.posts = posts
                        st.success(f"Found {len(posts)} {post_type}(s)")
                    else:
                        st.warning(f"No {post_type}s found matching your criteria")
    
    with fetch_col2:
        st.download_button(
            label="Export Results",
            data=json.dumps(st.session_state.posts, indent=2) if 'posts' in st.session_state and st.session_state.posts else "[]",
            file_name=f"{post_type}_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            disabled=not ('posts' in st.session_state and st.session_state.posts)
        )
    
    # Display posts in a table
    if 'posts' in st.session_state and st.session_state.posts:
        # Create a dataframe for the posts
        post_data = []
        for post in st.session_state.posts:
            post_item = {
                "ID": post.get("id"),
                "Title": post.get("title", {}).get("rendered", "No Title"),
                "Status": post.get("status", "").capitalize(),
                "Date": post.get("date", "")
            }
            post_data.append(post_item)
        
        # Sort the data
        df = pd.DataFrame(post_data)
        if sort_by == "Date (Newest)":
            df = df.sort_values(by="Date", ascending=False)
        elif sort_by == "Date (Oldest)":
            df = df.sort_values(by="Date", ascending=True)
        elif sort_by == "Title (A-Z)":
            df = df.sort_values(by="Title", ascending=True)
        elif sort_by == "Title (Z-A)":
            df = df.sort_values(by="Title", ascending=False)
        
        # Display the dataframe
        st.dataframe(df, use_container_width=True)
        
        # Post details section
        st.markdown('<p class="sub-header">Post Details</p>', unsafe_allow_html=True)
        
        # Select a post to view details
        selected_post_id = st.selectbox("Select a post to view details", 
                                       [f"{p['ID']} - {p['Title']}" for p in post_data])
        
        if selected_post_id:
            post_id = int(selected_post_id.split(" - ")[0])
            selected_post = next((p for p in st.session_state.posts if p["id"] == post_id), None)
            
            if selected_post:
                # Post actions
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    if st.button("Edit Post", use_container_width=True):
                        st.session_state.current_template = "Custom"
                        st.session_state.edit_post = selected_post
                        st.info("Post loaded for editing in the 'Create Post' tab")
                
                with col2:
                    if st.button("View on Site", use_container_width=True):
                        if "link" in selected_post:
                            st.markdown(f"[Open Post on Site]({selected_post['link']})")
                        else:
                            st.warning("Post link not available")
                
                with col3:
                    if st.button("Duplicate Post", use_container_width=True):
                        # Create a duplicate with a new title
                        duplicate_post = selected_post.copy()
                        if "title" in duplicate_post and "rendered" in duplicate_post["title"]:
                            duplicate_post["title"] = f"Copy of {duplicate_post['title']['rendered']}"
                        st.session_state.current_template = "Custom"
                        st.session_state.edit_post = duplicate_post
                        st.info("Post duplicated and loaded for editing in the 'Create Post' tab")
                
                with col4:
                    if st.button("Delete Post", use_container_width=True):
                        if st.session_state.connection_status:
                            confirm = st.checkbox("Confirm deletion")
                            if confirm:
                                auth_token = st.session_state.auth_token if auth_method == "JWT/OAuth" else None
                                result = delete_post(wp_url, post_type, post_id, username, password, auth_token)
                                if result:
                                    st.success("Post deleted successfully")
                                    # Remove from session state
                                    st.session_state.posts = [p for p in st.session_state.posts if p["id"] != post_id]
                        else:
                            st.warning("Please test your connection before deleting posts")
                
                # Post content tabs
                post_tab1, post_tab2, post_tab3 = st.tabs(["Content", "ACPT Meta Fields", "Raw JSON"])
                
                with post_tab1:
                    # Display post content
                    st.markdown(f"### {selected_post.get('title', {}).get('rendered', 'No Title')}")
                    st.markdown(f"**Status:** {selected_post.get('status', '').capitalize()}")
                    st.markdown(f"**Date:** {selected_post.get('date', '')}")
                    
                    # Display content
                    if "content" in selected_post and "rendered" in selected_post["content"]:
                        st.markdown(selected_post["content"]["rendered"], unsafe_allow_html=True)
                    else:
                        st.info("No content available")
                
                with post_tab2:
                    # Display ACPT meta fields
                    if "acpt" in selected_post:
                        acpt_data = selected_post["acpt"]
                        
                        # Display meta fields
                        if "meta" in acpt_data and acpt_data["meta"]:
                            for meta_box in acpt_data["meta"]:
                                if "meta_box" in meta_box:
                                    st.markdown(f"### {meta_box['meta_box']}")
                                    
                                    if "meta_fields" in meta_box:
                                        for field in meta_box["meta_fields"]:
                                            field_name = field.get('name', '')
                                            field_type = field.get('type', '')
                                            field_value = field.get('value', '')
                                            
                                            # Format the value based on type
                                            if isinstance(field_value, list):
                                                field_value_display = ", ".join([str(v) for v in field_value])
                                            else:
                                                field_value_display = field_value
                                            
                                            st.markdown(f"**{field_name}** ({field_type}): {field_value_display}")
                        
                        # Display WooCommerce product data if available
                        if "wc_product_data" in acpt_data and acpt_data["wc_product_data"]:
                            st.markdown("### WooCommerce Product Data")
                            
                            for product_data in acpt_data["wc_product_data"]:
                                st.markdown(f"#### {product_data.get('name', '')}")
                                
                                if "fields" in product_data:
                                    for field in product_data["fields"]:
                                        field_name = field.get('name', '')
                                        field_type = field.get('type', '')
                                        field_value = field.get('value', '')
                                        
                                        # Format the value based on type
                                        if isinstance(field_value, list):
                                            field_value_display = ", ".join([str(v) for v in field_value])
                                        else:
                                            field_value_display = field_value
                                        
                                        st.markdown(f"**{field_name}** ({field_type}): {field_value_display}")
                    else:
                        st.info("No ACPT meta fields available")
                
                with post_tab3:
                    # Display raw JSON
                    st.json(selected_post)

# Tab 2: Create Post
with tab2:
    st.markdown('<p class="sub-header">Create or Edit Post</p>', unsafe_allow_html=True)
    
    # Check if we're editing a post
    editing_post = False
    post_id = None
    if 'edit_post' in st.session_state and st.session_state.edit_post:
        editing_post = True
        post_id = st.session_state.edit_post.get("id")
        st.info(f"Editing post: {st.session_state.edit_post.get('title', {}).get('rendered', 'No Title')}")
    
    # Load template if selected
    if st.session_state.current_template and st.session_state.current_template != "Custom":
        template_data = get_template_data(st.session_state.current_template)
        st.success(f"Using template: {st.session_state.current_template}")
    elif editing_post:
        # Use the post data as template
        template_data = {
            "title": st.session_state.edit_post.get("title", {}).get("rendered", ""),
            "content": st.session_state.edit_post.get("content", {}).get("rendered", ""),
            "status": st.session_state.edit_post.get("status", "draft"),
            "acpt": st.session_state.edit_post.get("acpt", {"meta": []})
        }
    else:
        # Empty template
        template_data = {
            "title": "",
            "content": "",
            "status": "draft",
            "acpt": {
                "meta": []
            }
        }
    
    # Basic post information
    post_title = st.text_input("Post Title", value=template_data.get("title", ""))
    post_content = st.text_area("Post Content", value=template_data.get("content", ""), height=200)
    post_status = st.selectbox("Post Status", ["draft", "publish", "pending", "private"], 
                              index=["draft", "publish", "pending", "private"].index(template_data.get("status", "draft")))
    
    # ACPT Meta Fields
    st.markdown('<p class="sub-header">ACPT Meta Fields</p>', unsafe_allow_html=True)
    
    # Extract meta boxes and fields from template
    template_meta_boxes = {}
    if "acpt" in template_data and "meta" in template_data["acpt"]:
        for meta_item in template_data["acpt"]["meta"]:
            if "box" in meta_item and "field" in meta_item:
                box_name = meta_item["box"]
                field_name = meta_item["field"]
                field_value = meta_item.get("value", "")
                
                if box_name not in template_meta_boxes:
                    template_meta_boxes[box_name] = []
                
                # Check if field already exists
                field_exists = False
                for field in template_meta_boxes[box_name]:
                    if field["name"] == field_name:
                        field_exists = True
                        break
                
                if not field_exists:
                    # Determine field type based on value
                    field_type = "Text"
                    if isinstance(field_value, int):
                        field_type = "Number"
                    elif isinstance(field_value, list):
                        field_type = "Select Multiple"
                    elif isinstance(field_value, bool):
                        field_type = "Checkbox"
                    
                    template_meta_boxes[box_name].append({
                        "name": field_name,
                        "type": field_type,
                        "value": field_value
                    })
    
    # Allow adding/editing meta boxes
    meta_boxes = {}
    
    # Add meta boxes from template
    for box_name, fields in template_meta_boxes.items():
        meta_boxes[box_name] = fields
    
    # UI for managing meta boxes
    with st.expander("Manage Meta Boxes", expanded=True):
        # Add new meta box
        new_box_name = st.text_input("New Meta Box Name")
        if st.button("Add Meta Box") and new_box_name:
            if new_box_name not in meta_boxes:
                meta_boxes[new_box_name] = []
                st.success(f"Meta box '{new_box_name}' added")
            else:
                st.warning(f"Meta box '{new_box_name}' already exists")
    
    # Display meta boxes and fields
    for box_name, fields in meta_boxes.items():
        with st.expander(f"Meta Box: {box_name}", expanded=True):
            st.markdown(f"### {box_name}")
            
            # Add new field to this meta box
            col1, col2, col3 = st.columns(3)
            
            with col1:
                new_field_name = st.text_input("Field Name", key=f"new_field_name_{box_name}")
            
            with col2:
                new_field_type = st.selectbox("Field Type", 
                                             ["Text", "Textarea", "Number", "Select", "Select Multiple", "Checkbox", "Radio", "Date", "URL", "Email"],
                                             key=f"new_field_type_{box_name}")
            
            with col3:
                if st.button("Add Field", key=f"add_field_{box_name}"):
                    if new_field_name:
                        # Check if field already exists
                        field_exists = False
                        for field in fields:
                            if field["name"] == new_field_name:
                                field_exists = True
                                break
                        
                        if not field_exists:
                            # Initialize with empty value based on type
                            default_value = ""
                            if new_field_type == "Number":
                                default_value = 0
                            elif new_field_type in ["Select Multiple"]:
                                default_value = []
                            elif new_field_type == "Checkbox":
                                default_value = False
                            
                            fields.append({
                                "name": new_field_name,
                                "type": new_field_type,
                                "value": default_value
                            })
                            st.success(f"Field '{new_field_name}' added")
                        else:
                            st.warning(f"Field '{new_field_name}' already exists")
            
            # Display and edit fields
            if fields:
                for i, field in enumerate(fields):
                    col1, col2, col3 = st.columns([3, 6, 1])
                    
                    with col1:
                        st.markdown(f"**{field['name']}** ({field['type']})")
                    
                    with col2:
                        # Different input based on field type
                        field_key = f"{box_name}_{field['name']}_{i}"
                        
                        if field['type'] == "Text":
                            fields[i]['value'] = st.text_input("Value", value=field['value'], key=field_key)
                        elif field['type'] == "Textarea":
                            fields[i]['value'] = st.text_area("Value", value=field['value'], key=field_key)
                        elif field['type'] == "Number":
                            fields[i]['value'] = st.number_input("Value", value=float(field['value']) if field['value'] else 0, key=field_key)
                        elif field['type'] == "Date":
                            date_value = field['value'] if field['value'] else datetime.now().strftime("%Y-%m-%d")
                            fields[i]['value'] = st.date_input("Value", value=datetime.strptime(date_value, "%Y-%m-%d") if isinstance(date_value, str) else date_value, key=field_key).strftime("%Y-%m-%d")
                        elif field['type'] == "URL":
                            fields[i]['value'] = st.text_input("Value (URL)", value=field['value'], key=field_key)
                        elif field['type'] == "Email":
                            fields[i]['value'] = st.text_input("Value (Email)", value=field['value'], key=field_key)
                        elif field['type'] in ["Select", "Select Multiple", "Radio"]:
                            # Options input
                            if isinstance(field['value'], list) and field['type'] == "Select Multiple":
                                current_options = field['value']
                            elif isinstance(field['value'], str) and field['type'] in ["Select", "Radio"]:
                                current_options = [field['value']]
                            else:
                                current_options = []
                            
                            options_text = st.text_area("Options (one per line)", 
                                                      value="\n".join(current_options) if current_options else "", 
                                                      key=f"options_{field_key}")
                            options = [opt.strip() for opt in options_text.split("\n") if opt.strip()]
                            
                            if field['type'] == "Select":
                                fields[i]['value'] = st.selectbox("Value", options, 
                                                                index=options.index(field['value']) if field['value'] in options else 0,
                                                                key=f"value_{field_key}")
                            elif field['type'] == "Select Multiple":
                                selected_options = []
                                for opt in options:
                                    if st.checkbox(opt, value=opt in field['value'] if isinstance(field['value'], list) else False, 
                                                 key=f"checkbox_{field_key}_{opt}"):
                                        selected_options.append(opt)
                                fields[i]['value'] = selected_options
                            elif field['type'] == "Radio":
                                fields[i]['value'] = st.radio("Value", options, 
                                                            index=options.index(field['value']) if field['value'] in options else 0,
                                                            key=f"radio_{field_key}")
                        elif field['type'] == "Checkbox":
                            fields[i]['value'] = st.checkbox("Value", value=bool(field['value']), key=field_key)
                    
                    with col3:
                        if st.button("🗑️", key=f"delete_{field_key}"):
                            fields.pop(i)
                            st.success(f"Field '{field['name']}' deleted")
                            st.experimental_rerun()
            else:
                st.info("No fields in this meta box. Add a field using the form above.")
    
    # Create post button
    st.markdown('<p class="sub-header">Save Post</p>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Preview JSON", use_container_width=True):
            # Prepare post data
            post_data = {
                "title": post_title,
                "content": post_content,
                "status": post_status,
                "acpt": {
                    "meta": []
                }
            }
            
            # Add ACPT meta data in the format required by the API
            for box_name, fields in meta_boxes.items():
                for field in fields:
                    post_data["acpt"]["meta"].append({
                        "box": box_name,
                        "field": field["name"],
                        "value": field["value"]
                    })
            
            # Show the JSON that will be sent
            st.json(post_data)
    
    with col2:
        button_text = "Update Post" if editing_post else "Create Post"
        if st.button(button_text, use_container_width=True):
            if not wp_url:
                st.warning("Please enter a WordPress URL")
            elif not post_title:
                st.warning("Please enter a post title")
            elif not st.session_state.connection_status:
                st.warning("Please test your connection before creating/updating posts")
            else:
                # Prepare post data
                post_data = {
                    "title": post_title,
                    "content": post_content,
                    "status": post_status,
                    "acpt": {
                        "meta": []
                    }
                }
                
                # Add ACPT meta data in the format required by the API
                for box_name, fields in meta_boxes.items():
                    for field in fields:
                        post_data["acpt"]["meta"].append({
                            "box": box_name,
                            "field": field["name"],
                            "value": field["value"]
                        })
                
                # Get authentication details
                auth_token = st.session_state.auth_token if auth_method == "JWT/OAuth" else None
                
                # Create or update the post
                with st.spinner(f"{'Updating' if editing_post else 'Creating'} post..."):
                    if editing_post and post_id:
                        result = update_post(wp_url, post_type, post_id, post_data, username, password, auth_token)
                        success_message = "Post updated successfully!"
                    else:
                        result = create_post(wp_url, post_type, post_data, username, password, auth_token)
                        success_message = "Post created successfully!"
                    
                    if result:
                        st.success(f"{success_message} ID: {result.get('id')}")
                        
                        # Clear edit state if we were editing
                        if 'edit_post' in st.session_state:
                            del st.session_state.edit_post
                        
                        # Show the result
                        st.json(result)
                        
                        # Add to session state posts if we're viewing posts
                        if 'posts' in st.session_state and st.session_state.posts:
                            # Remove old version if updating
                            if editing_post and post_id:
                                st.session_state.posts = [p for p in st.session_state.posts if p["id"] != post_id]
                            
                            # Add new version
                            st.session_state.posts.append(result)

# Tab 3: Visualize Data
with tab3:
    st.markdown('<p class="sub-header">Data Visualization</p>', unsafe_allow_html=True)
    
    # Select visualization type
    viz_type = st.selectbox("Select Visualization Type", 
                           ["Template-based Visualization", "Custom Visualization"])
    
    if viz_type == "Template-based Visualization":
        # Use template for visualization
        if st.session_state.current_template:
            st.success(f"Using template: {st.session_state.current_template}")
            
            # Generate sample data for the template
            sample_data = generate_sample_data(st.session_state.current_template)
            
            # Create visualizations based on the template
            create_visualizations(st.session_state.current_template, sample_data)
        else:
            st.info("Please select a template from the sidebar to visualize template-specific data")
    
    elif viz_type == "Custom Visualization":
        # Custom visualization options
        if 'posts' in st.session_state and st.session_state.posts:
            st.success(f"Using {len(st.session_state.posts)} posts for visualization")
            
            # Select visualization
            viz_option = st.selectbox("Select Visualization", 
                                     ["Post Status Distribution", "Posts by Date", "Meta Field Analysis"])
            
            if viz_option == "Post Status Distribution":
                # Count posts by status
                status_counts = {}
                for post in st.session_state.posts:
                    status = post.get("status", "unknown").capitalize()
                    status_counts[status] = status_counts.get(status, 0) + 1
                
                # Create dataframe
                status_df = pd.DataFrame({
                    "Status": list(status_counts.keys()),
                    "Count": list(status_counts.values())
                })
                
                # Create visualization
                fig = px.pie(status_df, values="Count", names="Status", title="Post Status Distribution")
                st.plotly_chart(fig, use_container_width=True)
            
            elif viz_option == "Posts by Date":
                # Extract dates
                dates = []
                for post in st.session_state.posts:
                    date_str = post.get("date", "")
                    if date_str:
                        try:
                            date = datetime.strptime(date_str.split("T")[0], "%Y-%m-%d")
                            dates.append(date)
                        except:
                            pass
                
                # Create dataframe
                date_df = pd.DataFrame({"Date": dates})
                date_df["Month"] = date_df["Date"].dt.strftime("%Y-%m")
                
                # Count posts by month
                month_counts = date_df["Month"].value_counts().reset_index()
                month_counts.columns = ["Month", "Count"]
                month_counts = month_counts.sort_values("Month")
                
                # Create visualization
                fig = px.bar(month_counts, x="Month", y="Count", title="Posts by Month")
                st.plotly_chart(fig, use_container_width=True)
            
            elif viz_option == "Meta Field Analysis":
                # Select meta box and field
                meta_boxes = set()
                meta_fields = {}
                
                for post in st.session_state.posts:
                    if "acpt" in post and "meta" in post["acpt"]:
                        for meta_item in post["acpt"]["meta"]:
                            if isinstance(meta_item, dict) and "box" in meta_item and "field" in meta_item:
                                box_name = meta_item["box"]
                                field_name = meta_item["field"]
                                
                                meta_boxes.add(box_name)
                                
                                if box_name not in meta_fields:
                                    meta_fields[box_name] = set()
                                
                                meta_fields[box_name].add(field_name)
                
                if meta_boxes:
                    selected_box = st.selectbox("Select Meta Box", list(meta_boxes))
                    
                    if selected_box in meta_fields and meta_fields[selected_box]:
                        selected_field = st.selectbox("Select Field", list(meta_fields[selected_box]))
                        
                        # Extract field values
                        field_values = []
                        for post in st.session_state.posts:
                            if "acpt" in post and "meta" in post["acpt"]:
                                for meta_item in post["acpt"]["meta"]:
                                    if isinstance(meta_item, dict) and "box" in meta_item and "field" in meta_item:
                                        if meta_item["box"] == selected_box and meta_item["field"] == selected_field:
                                            field_values.append({
                                                "Post ID": post.get("id"),
                                                "Post Title": post.get("title", {}).get("rendered", "No Title"),
                                                "Value": meta_item.get("value", "")
                                            })
                        
                        if field_values:
                            # Create dataframe
                            field_df = pd.DataFrame(field_values)
                            
                            # Determine visualization based on value type
                            sample_value = field_values[0]["Value"] if field_values else None
                            
                            if isinstance(sample_value, (int, float)):
                                # Numeric visualization
                                st.subheader(f"Distribution of {selected_field} values")
                                fig = px.histogram(field_df, x="Value", title=f"Distribution of {selected_field}")
                                st.plotly_chart(fig, use_container_width=True)
                                
                                # Summary statistics
                                st.subheader("Summary Statistics")
                                st.dataframe(field_df["Value"].describe().reset_index())
                            
                            elif isinstance(sample_value, str):
                                # Text visualization - count unique values
                                value_counts = field_df["Value"].value_counts().reset_index()
                                value_counts.columns = ["Value", "Count"]
                                
                                st.subheader(f"Most common {selected_field} values")
                                fig = px.bar(value_counts.head(10), x="Value", y="Count", title=f"Top {selected_field} values")
                                st.plotly_chart(fig, use_container_width=True)
                            
                            elif isinstance(sample_value, list):
                                # List visualization - flatten and count
                                all_values = []
                                for values in field_df["Value"]:
                                    if isinstance(values, list):
                                        all_values.extend(values)
                                
                                value_counts = pd.Series(all_values).value_counts().reset_index()
                                value_counts.columns = ["Value", "Count"]
                                
                                st.subheader(f"Most common {selected_field} values")
                                fig = px.bar(value_counts.head(10), x="Value", y="Count", title=f"Top {selected_field} values")
                                st.plotly_chart(fig, use_container_width=True)
                            
                            # Raw data
                            st.subheader("Raw Data")
                            st.dataframe(field_df)
                        else:
                            st.info(f"No values found for field {selected_field}")
                    else:
                        st.info("No fields found in the selected meta box")
                else:
                    st.info("No meta boxes found in the posts")
        else:
            st.warning("Please fetch posts in the 'View Posts' tab before creating visualizations")

# Tab 4: Export/Import
with tab4:
    st.markdown('<p class="sub-header">Export and Import Data</p>', unsafe_allow_html=True)
    
    export_tab, import_tab = st.tabs(["Export", "Import"])
    
    with export_tab:
        st.markdown("### Export Options")
        
        export_type = st.radio("What would you like to export?", 
                              ["Template", "Current Post", "All Fetched Posts", "Custom Query"])
        
        if export_type == "Template":
            # Export template
            if st.session_state.current_template:
                template_data = get_template_data(st.session_state.current_template)
                
                st.subheader("Template JSON")
                st.json(template_data)
                
                # Download button
                json_str = json.dumps(template_data, indent=2)
                b64 = base64.b64encode(json_str.encode()).decode()
                href = f'<a href="data:application/json;base64,{b64}" download="template_{st.session_state.current_template.replace(" ", "_").lower()}.json">Download Template JSON</a>'
                st.markdown(href, unsafe_allow_html=True)
            else:
                st.info("Please select a template from the sidebar")
        
        elif export_type == "Current Post":
            # Export current post being edited
            if 'edit_post' in st.session_state and st.session_state.edit_post:
                post_data = st.session_state.edit_post
                
                st.subheader("Post JSON")
                st.json(post_data)
                
                # Download button
                json_str = json.dumps(post_data, indent=2)
                b64 = base64.b64encode(json_str.encode()).decode()
                href = f'<a href="data:application/json;base64,{b64}" download="post_{post_data.get("id", "export")}.json">Download Post JSON</a>'
                st.markdown(href, unsafe_allow_html=True)
            else:
                st.info("No post is currently being edited. Go to the 'View Posts' tab and select a post to edit")
        
        elif export_type == "All Fetched Posts":
            # Export all fetched posts
            if 'posts' in st.session_state and st.session_state.posts:
                st.success(f"Exporting {len(st.session_state.posts)} posts")
                
                # Options for export format
                export_format = st.radio("Export Format", ["Full JSON", "Simplified JSON", "CSV"])
                
                if export_format == "Full JSON":
                    # Full JSON export
                    json_str = json.dumps(st.session_state.posts, indent=2)
                    b64 = base64.b64encode(json_str.encode()).decode()
                    href = f'<a href="data:application/json;base64,{b64}" download="{post_type}_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json">Download Full JSON</a>'
                    st.markdown(href, unsafe_allow_html=True)
                
                elif export_format == "Simplified JSON":
                    # Simplified JSON with just the essential fields
                    simplified_posts = []
                    for post in st.session_state.posts:
                        simplified_post = {
                            "id": post.get("id"),
                            "title": post.get("title", {}).get("rendered", "No Title"),
                            "status": post.get("status", ""),
                            "date": post.get("date", ""),
                            "content": post.get("content", {}).get("rendered", ""),
                            "acpt": post.get("acpt", {})
                        }
                        simplified_posts.append(simplified_post)
                    
                    json_str = json.dumps(simplified_posts, indent=2)
                    b64 = base64.b64encode(json_str.encode()).decode()
                    href = f'<a href="data:application/json;base64,{b64}" download="{post_type}_simplified_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json">Download Simplified JSON</a>'
                    st.markdown(href, unsafe_allow_html=True)
                
                elif export_format == "CSV":
                    # CSV export with flattened meta fields
                    csv_data = []
                    for post in st.session_state.posts:
                        post_data = {
                            "ID": post.get("id"),
                            "Title": post.get("title", {}).get("rendered", "No Title"),
                            "Status": post.get("status", ""),
                            "Date": post.get("date", "")
                        }
                        
                        # Add ACPT meta fields
                        if "acpt" in post and "meta" in post["acpt"]:
                            for meta_item in post["acpt"]["meta"]:
                                if isinstance(meta_item, dict) and "box" in meta_item and "field" in meta_item:
                                    field_key = f"{meta_item['box']}_{meta_item['field']}"
                                    field_value = meta_item.get("value", "")
                                    
                                    # Convert lists to comma-separated strings
                                    if isinstance(field_value, list):
                                        field_value = ", ".join([str(v) for v in field_value])
                                    
                                    post_data[field_key] = field_value
                        
                        csv_data.append(post_data)
                    
                    # Convert to DataFrame and then to CSV
                    df = pd.DataFrame(csv_data)
                    csv = df.to_csv(index=False)
                    b64 = base64.b64encode(csv.encode()).decode()
                    href = f'<a href="data:text/csv;base64,{b64}" download="{post_type}_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv">Download CSV</a>'
                    st.markdown(href, unsafe_allow_html=True)
            else:
                st.info("No posts have been fetched. Go to the 'View Posts' tab and fetch posts first")
        
        elif export_type == "Custom Query":
            # Custom query export
            st.subheader("Custom Query Export")
            
            # Query parameters
            col1, col2 = st.columns(2)
            
            with col1:
                query_post_type = st.selectbox("Post Type", ["post", "product", "page", "property", "stock", "assessment", "custom"])
                
                if query_post_type == "custom":
                    query_post_type = st.text_input("Enter Custom Post Type")
            
            with col2:
                query_status = st.selectbox("Status", ["Any", "publish", "draft", "pending", "private"])
            
            query_limit = st.slider("Number of Posts", min_value=1, max_value=100, value=10)
            
            # Execute query button
            if st.button("Execute Query and Export"):
                if not wp_url:
                    st.warning("Please enter a WordPress URL")
                elif not st.session_state.connection_status:
                    st.warning("Please test your connection before executing queries")
                else:
                    with st.spinner("Executing query..."):
                        # Prepare parameters
                        params = {
                            "per_page": query_limit
                        }
                        
                        if query_status != "Any":
                            params["status"] = query_status
                        
                        # Get authentication details
                        auth_token = st.session_state.auth_token if auth_method == "JWT/OAuth" else None
                        
                        # Execute query
                        query_results = get_posts(wp_url, query_post_type, username, password, auth_token, params)
                        
                        if query_results:
                            st.success(f"Query returned {len(query_results)} results")
                            
                            # Display results
                            with st.expander("View Results", expanded=True):
                                st.json(query_results)
                            
                            # Export options
                            export_format = st.radio("Export Format", ["JSON", "CSV"])
                            
                            if export_format == "JSON":
                                json_str = json.dumps(query_results, indent=2)
                                b64 = base64.b64encode(json_str.encode()).decode()
                                href = f'<a href="data:application/json;base64,{b64}" download="query_results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json">Download JSON Results</a>'
                                st.markdown(href, unsafe_allow_html=True)
                            
                            elif export_format == "CSV":
                                # Flatten results for CSV
                                csv_data = []
                                for post in query_results:
                                    post_data = {
                                        "ID": post.get("id"),
                                        "Title": post.get("title", {}).get("rendered", "No Title"),
                                        "Status": post.get("status", ""),
                                        "Date": post.get("date", "")
                                    }
                                    
                                    # Add ACPT meta fields
                                    if "acpt" in post and "meta" in post["acpt"]:
                                        for meta_item in post["acpt"]["meta"]:
                                            if isinstance(meta_item, dict) and "box" in meta_item and "field" in meta_item:
                                                field_key = f"{meta_item['box']}_{meta_item['field']}"
                                                field_value = meta_item.get("value", "")
                                                
                                                # Convert lists to comma-separated strings
                                                if isinstance(field_value, list):
                                                    field_value = ", ".join([str(v) for v in field_value])
                                                
                                                post_data[field_key] = field_value
                                    
                                    csv_data.append(post_data)
                                
                                # Convert to DataFrame and then to CSV
                                df = pd.DataFrame(csv_data)
                                csv = df.to_csv(index=False)
                                b64 = base64.b64encode(csv.encode()).decode()
                                href = f'<a href="data:text/csv;base64,{b64}" download="query_results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv">Download CSV Results</a>'
                                st.markdown(href, unsafe_allow_html=True)
                        else:
                            st.warning("Query returned no results")
    
    with import_tab:
        st.markdown("### Import Options")
        
        import_type = st.radio("What would you like to import?", 
                              ["JSON Template", "JSON Post", "Bulk Import"])
        
        if import_type == "JSON Template":
            # Import JSON template
            st.subheader("Import JSON Template")
            
            template_json = st.text_area("Paste JSON Template", height=300)
            
            if st.button("Load Template"):
                if template_json:
                    try:
                        template_data = json.loads(template_json)
                        
                        # Validate template structure
                        if "title" in template_data and "content" in template_data and "acpt" in template_data:
                            st.session_state.current_template = "Custom"
                            st.session_state.edit_post = template_data
                            st.success("Template loaded successfully! Go to the 'Create Post' tab to use it")
                        else:
                            st.error("Invalid template format. Template must include title, content, and acpt fields")
                    except json.JSONDecodeError:
                        st.error("Invalid JSON format. Please check your input")
        
        elif import_type == "JSON Post":
            # Import JSON post
            st.subheader("Import JSON Post")
            
            post_json = st.text_area("Paste JSON Post", height=300)
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("Preview Post"):
                    if post_json:
                        try:
                            post_data = json.loads(post_json)
                            
                            # Display preview
                            st.subheader("Post Preview")
                            
                            if "title" in post_data:
                                if isinstance(post_data["title"], dict) and "rendered" in post_data["title"]:
                                    st.markdown(f"**Title:** {post_data['title']['rendered']}")
                                else:
                                    st.markdown(f"**Title:** {post_data['title']}")
                            
                            if "content" in post_data:
                                if isinstance(post_data["content"], dict) and "rendered" in post_data["content"]:
                                    st.markdown(f"**Content:** {post_data['content']['rendered']}", unsafe_allow_html=True)
                                else:
                                    st.markdown(f"**Content:** {post_data['content']}", unsafe_allow_html=True)
                            
                            if "acpt" in post_data and "meta" in post_data["acpt"]:
                                st.markdown("**ACPT Meta Fields:**")
                                
                                for meta_item in post_data["acpt"]["meta"]:
                                    if isinstance(meta_item, dict):
                                        if "box" in meta_item and "field" in meta_item:
                                            box = meta_item["box"]
                                            field = meta_item["field"]
                                            value = meta_item.get("value", "")
                                            
                                            # Format value for display
                                            if isinstance(value, list):
                                                value_display = ", ".join([str(v) for v in value])
                                            else:
                                                value_display = value
                                            
                                            st.markdown(f"- **{box} / {field}:** {value_display}")
                        except json.JSONDecodeError:
                            st.error("Invalid JSON format. Please check your input")
            
            with col2:
                if st.button("Load for Editing"):
                    if post_json:
                        try:
                            post_data = json.loads(post_json)
                            
                            # Validate post structure
                            if ("title" in post_data or ("title" in post_data and "rendered" in post_data["title"])) and "acpt" in post_data:
                                st.session_state.current_template = "Custom"
                                st.session_state.edit_post = post_data
                                st.success("Post loaded successfully! Go to the 'Create Post' tab to edit it")
                            else:
                                st.error("Invalid post format. Post must include title and acpt fields")
                        except json.JSONDecodeError:
                            st.error("Invalid JSON format. Please check your input")
        
        elif import_type == "Bulk Import":
            # Bulk import
            st.subheader("Bulk Import")
            
            import_method = st.radio("Import Method", ["Upload JSON File", "Paste JSON Array"])
            
            if import_method == "Upload JSON File":
                uploaded_file = st.file_uploader("Upload JSON File", type=["json"])
                
                if uploaded_file is not None:
                    try:
                        import_data = json.load(uploaded_file)
                        
                        if isinstance(import_data, list):
                            st.success(f"Loaded {len(import_data)} items from file")
                            
                            # Preview the data
                            with st.expander("Preview Import Data"):
                                st.write(f"First item in the import:")
                                st.json(import_data[0] if import_data else {})
                            
                            # Import options
                            st.subheader("Import Options")
                            
                            import_post_type = st.selectbox("Post Type for Import", ["post", "product", "page", "property", "stock", "assessment", "custom"])
                            
                            if import_post_type == "custom":
                                import_post_type = st.text_input("Enter Custom Post Type")
                            
                            # Execute import button
                            if st.button("Execute Bulk Import"):
                                if not wp_url:
                                    st.warning("Please enter a WordPress URL")
                                elif not st.session_state.connection_status:
                                    st.warning("Please test your connection before importing")
                                else:
                                    # Create progress bar
                                    progress_bar = st.progress(0)
                                    status_text = st.empty()
                                    
                                    # Get authentication details
                                    auth_token = st.session_state.auth_token if auth_method == "JWT/OAuth" else None
                                    
                                    # Import each item
                                    success_count = 0
                                    error_count = 0
                                    
                                    for i, item in enumerate(import_data):
                                        # Update progress
                                        progress = (i + 1) / len(import_data)
                                        progress_bar.progress(progress)
                                        status_text.text(f"Importing item {i+1} of {len(import_data)}")
                                        
                                        # Create post
                                        result = create_post(wp_url, import_post_type, item, username, password, auth_token)
                                        
                                        if result:
                                            success_count += 1
                                        else:
                                            error_count += 1
                                    
                                    # Final status
                                    st.success(f"Import completed: {success_count} successful, {error_count} failed")
                        else:
                            st.error("Invalid import format. Expected a JSON array")
                    except json.JSONDecodeError:
                        st.error("Invalid JSON file. Please check the file format")
            
            elif import_method == "Paste JSON Array":
                import_json = st.text_area("Paste JSON Array", height=300)
                
                if st.button("Validate Import Data"):
                    if import_json:
                        try:
                            import_data = json.loads(import_json)
                            
                            if isinstance(import_data, list):
                                st.success(f"Valid JSON array with {len(import_data)} items")
                                
                                # Preview the data
                                with st.expander("Preview Import Data"):
                                    st.write(f"First item in the import:")
                                    st.json(import_data[0] if import_data else {})
                                
                                # Import options
                                st.subheader("Import Options")
                                
                                import_post_type = st.selectbox("Post Type for Import", ["post", "product", "page", "property", "stock", "assessment", "custom"])
                                
                                if import_post_type == "custom":
                                    import_post_type = st.text_input("Enter Custom Post Type")
                                
                                # Execute import button
                                if st.button("Execute Bulk Import from JSON"):
                                    if not wp_url:
                                        st.warning("Please enter a WordPress URL")
                                    elif not st.session_state.connection_status:
                                        st.warning("Please test your connection before importing")
                                    else:
                                        # Create progress bar
                                        progress_bar = st.progress(0)
                                        status_text = st.empty()
                                        
                                        # Get authentication details
                                        auth_token = st.session_state.auth_token if auth_method == "JWT/OAuth" else None
                                        
                                        # Import each item
                                        success_count = 0
                                        error_count = 0
                                        
                                        for i, item in enumerate(import_data):
                                            # Update progress
                                            progress = (i + 1) / len(import_data)
                                            progress_bar.progress(progress)
                                            status_text.text(f"Importing item {i+1} of {len(import_data)}")
                                            
                                            # Create post
                                            result = create_post(wp_url, import_post_type, item, username, password, auth_token)
                                            
                                            if result:
                                                success_count += 1
                                            else:
                                                error_count += 1
                                        
                                        # Final status
                                        st.success(f"Import completed: {success_count} successful, {error_count} failed")
                            else:
                                st.error("Invalid import format. Expected a JSON array")
                        except json.JSONDecodeError:
                            st.error("Invalid JSON format. Please check your input")

# Tab 5: Batch Operations
with tab5:
    st.markdown('<p class="sub-header">Batch Operations</p>', unsafe_allow_html=True)
    
    # Batch operation types
    operation_type = st.selectbox("Select Operation Type", 
                                 ["Bulk Create", "Bulk Update", "Bulk Delete"])
    
    if operation_type == "Bulk Create":
        st.subheader("Bulk Create Posts")
        
        # Template selection
        use_template = st.checkbox("Use Template for Bulk Creation")
        
        if use_template:
            if st.session_state.current_template:
                st.success(f"Using template: {st.session_state.current_template}")
                template_data = get_template_data(st.session_state.current_template)
            else:
                st.warning("Please select a template from the sidebar")
                template_data = {
                    "title": "",
                    "content": "",
                    "status": "draft",
                    "acpt": {
                        "meta": []
                    }
                }
        else:
            template_data = {
                "title": "",
                "content": "",
                "status": "draft",
                "acpt": {
                    "meta": []
                }
            }
        
        # Number of posts to create
        num_posts = st.number_input("Number of Posts to Create", min_value=1, max_value=100, value=5)
        
        # Base title and content
        base_title = st.text_input("Base Title", value=template_data.get("title", ""))
        base_content = st.text_area("Base Content", value=template_data.get("content", ""), height=100)
        post_status = st.selectbox("Post Status", ["draft", "publish", "pending", "private"], 
                                  index=["draft", "publish", "pending", "private"].index(template_data.get("status", "draft")))
        
        # Preview generation
        if st.button("Preview Generation"):
            st.subheader("Preview of Posts to be Created")
            
            for i in range(min(3, num_posts)):
                with st.expander(f"Post {i+1}: {base_title} {i+1}"):
                    st.markdown(f"**Title:** {base_title} {i+1}")
                    st.markdown(f"**Content:** {base_content}")
                    st.markdown(f"**Status:** {post_status}")
                    
                    if "acpt" in template_data and "meta" in template_data["acpt"]:
                        st.markdown("**ACPT Meta Fields:**")
                        
                        for meta_item in template_data["acpt"]["meta"]:
                            if "box" in meta_item and "field" in meta_item:
                                box = meta_item["box"]
                                field = meta_item["field"]
                                value = meta_item.get("value", "")
                                
                                # Format value for display
                                if isinstance(value, list):
                                    value_display = ", ".join([str(v) for v in value])
                                else:
                                    value_display = value
                                
                                st.markdown(f"- **{box} / {field}:** {value_display}")
            
            if num_posts > 3:
                st.info(f"... and {num_posts - 3} more posts")
        
        # Execute bulk creation
        if st.button("Execute Bulk Creation"):
            if not wp_url:
                st.warning("Please enter a WordPress URL")
            elif not base_title:
                st.warning("Please enter a base title")
            elif not st.session_state.connection_status:
                st.warning("Please test your connection before bulk operations")
            else:
                # Create progress bar
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # Get authentication details
                auth_token = st.session_state.auth_token if auth_method == "JWT/OAuth" else None
                
                # Create posts
                success_count = 0
                error_count = 0
                created_posts = []
                
                for i in range(num_posts):
                    # Update progress
                    progress = (i + 1) / num_posts
                    progress_bar.progress(progress)
                    status_text.text(f"Creating post {i+1} of {num_posts}")
                    
                    # Prepare post data
                    post_data = {
                        "title": f"{base_title} {i+1}",
                        "content": base_content,
                        "status": post_status,
                        "acpt": {
                            "meta": []
                        }
                    }
                    
                    # Add ACPT meta data from template
                    if "acpt" in template_data and "meta" in template_data["acpt"]:
                        for meta_item in template_data["acpt"]["meta"]:
                            if "box" in meta_item and "field" in meta_item:
                                post_data["acpt"]["meta"].append({
                                    "box": meta_item["box"],
                                    "field": meta_item["field"],
                                    "value": meta_item.get("value", "")
                                })
                    
                    # Create post
                    result = create_post(wp_url, post_type, post_data, username, password, auth_token)
                    
                    if result:
                        success_count += 1
                        created_posts.append(result)
                    else:
                        error_count += 1
                
                # Final status
                st.success(f"Bulk creation completed: {success_count} successful, {error_count} failed")
                
                # Add to session state
                if created_posts:
                    if 'posts' in st.session_state:
                        st.session_state.posts.extend(created_posts)
                    else:
                        st.session_state.posts = created_posts
    
    elif operation_type == "Bulk Update":
        st.subheader("Bulk Update Posts")
        
        # Check if we have posts
        if 'posts' in st.session_state and st.session_state.posts:
            st.success(f"Found {len(st.session_state.posts)} posts for potential update")
            
            # Select posts to update
            update_option = st.radio("Select Posts to Update", ["All Fetched Posts", "Filter by Status", "Select Individually"])
            
            selected_posts = []
            
            if update_option == "All Fetched Posts":
                selected_posts = st.session_state.posts
                st.info(f"Selected {len(selected_posts)} posts for update")
            
            elif update_option == "Filter by Status":
                status_filter = st.selectbox("Filter by Status", ["publish", "draft", "pending", "private"])
                selected_posts = [p for p in st.session_state.posts if p.get("status") == status_filter]
                st.info(f"Selected {len(selected_posts)} {status_filter} posts for update")
            
            elif update_option == "Select Individually":
                # Create a list of post titles with IDs
                post_options = {f"{p.get('id')} - {p.get('title', {}).get('rendered', 'No Title')}": p.get('id') 
                               for p in st.session_state.posts}
                
                selected_post_ids = st.multiselect("Select Posts to Update", 
                                                 list(post_options.keys()))
                
                # Get the selected posts
                post_ids = [post_options[title] for title in selected_post_ids]
                selected_posts = [p for p in st.session_state.posts if p.get("id") in post_ids]
                
                st.info(f"Selected {len(selected_posts)} posts for update")
            
            # Update options
            st.subheader("Update Options")
            
            update_fields = st.multiselect("Select Fields to Update", 
                                          ["Title", "Content", "Status", "ACPT Meta Fields"])
            
            if "Title" in update_fields:
                new_title = st.text_input("New Title (leave empty to keep original)")
            
            if "Content" in update_fields:
                new_content = st.text_area("New Content (leave empty to keep original)")
            
            if "Status" in update_fields:
                new_status = st.selectbox("New Status", ["publish", "draft", "pending", "private"])
            
            if "ACPT Meta Fields" in update_fields:
                st.markdown("### ACPT Meta Fields to Update")
                
                # Collect all meta boxes and fields from selected posts
                all_meta_boxes = {}
                
                for post in selected_posts:
                    if "acpt" in post and "meta" in post["acpt"]:
                        for meta_box in post["acpt"]["meta"]:
                            if "meta_box" in meta_box:
                                box_name = meta_box["meta_box"]
                                
                                if box_name not in all_meta_boxes:
                                    all_meta_boxes[box_name] = set()
                                
                                if "meta_fields" in meta_box:
                                    for field in meta_box["meta_fields"]:
                                        if "name" in field:
                                            all_meta_boxes[box_name].add(field["name"])
                
                # Select meta fields to update
                meta_updates = []
                
                for box_name, fields in all_meta_boxes.items():
                    with st.expander(f"Meta Box: {box_name}"):
                        st.markdown(f"### {box_name}")
                        
                        for field_name in fields:
                            if st.checkbox(f"Update {field_name}", key=f"update_{box_name}_{field_name}"):
                                field_value = st.text_input(f"New value for {field_name}", key=f"value_{box_name}_{field_name}")
                                
                                meta_updates.append({
                                    "box": box_name,
                                    "field": field_name,
                                    "value": field_value
                                })
            
            # Execute bulk update
            if st.button("Execute Bulk Update"):
                if not wp_url:
                    st.warning("Please enter a WordPress URL")
                elif not selected_posts:
                    st.warning("No posts selected for update")
                elif not update_fields:
                    st.warning("No fields selected for update")
                elif not st.session_state.connection_status:
                    st.warning("Please test your connection before bulk operations")
                else:
                    # Create progress bar
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    # Get authentication details
                    auth_token = st.session_state.auth_token if auth_method == "JWT/OAuth" else None
                    
                    # Update posts
                    success_count = 0
                    error_count = 0
                    
                    for i, post in enumerate(selected_posts):
                        # Update progress
                        progress = (i + 1) / len(selected_posts)
                        progress_bar.progress(progress)
                        status_text.text(f"Updating post {i+1} of {len(selected_posts)}")
                        
                        # Prepare update data
                        update_data = {}
                        
                        if "Title" in update_fields and new_title:
                            update_data["title"] = new_title
                        
                        if "Content" in update_fields and new_content:
                            update_data["content"] = new_content
                        
                        if "Status" in update_fields:
                            update_data["status"] = new_status
                        
                        if "ACPT Meta Fields" in update_fields and meta_updates:
                            update_data["acpt"] = {
                                "meta": meta_updates
                            }
                        
                        # Update post
                        result = update_post(wp_url, post_type, post.get("id"), update_data, username, password, auth_token)
                        
                        if result:
                            success_count += 1
                            
                            # Update in session state
                            for j, p in enumerate(st.session_state.posts):
                                if p.get("id") == post.get("id"):
                                    st.session_state.posts[j] = result
                                    break
                        else:
                            error_count += 1
                    
                    # Final status
                    st.success(f"Bulk update completed: {success_count} successful, {error_count} failed")
        else:
            st.warning("No posts have been fetched. Go to the 'View Posts' tab and fetch posts first")
    
    elif operation_type == "Bulk Delete":
        st.subheader("Bulk Delete Posts")
        
        # Check if we have posts
        if 'posts' in st.session_state and st.session_state.posts:
            st.success(f"Found {len(st.session_state.posts)} posts for potential deletion")
            
            # Select posts to delete
            delete_option = st.radio("Select Posts to Delete", ["Filter by Status", "Select Individually"])
            
            selected_posts = []
            
            if delete_option == "Filter by Status":
                status_filter = st.selectbox("Filter by Status", ["publish", "draft", "pending", "private"])
                selected_posts = [p for p in st.session_state.posts if p.get("status") == status_filter]
                st.info(f"Selected {len(selected_posts)} {status_filter} posts for deletion")
            
            elif delete_option == "Select Individually":
                # Create a list of post titles with IDs
                post_options = {f"{p.get('id')} - {p.get('title', {}).get('rendered', 'No Title')}": p.get('id') 
                               for p in st.session_state.posts}
                
                selected_post_ids = st.multiselect("Select Posts to Delete", 
                                                 list(post_options.keys()))
                
                # Get the selected posts
                post_ids = [post_options[title] for title in selected_post_ids]
                selected_posts = [p for p in st.session_state.posts if p.get("id") in post_ids]
                
                st.info(f"Selected {len(selected_posts)} posts for deletion")
            
            # Confirmation
            st.warning("⚠️ Warning: This operation will permanently delete the selected posts!")
            confirm = st.checkbox("I understand that this action cannot be undone")
            
            # Execute bulk deletion
            if st.button("Execute Bulk Deletion", disabled=not confirm):
                if not wp_url:
                    st.warning("Please enter a WordPress URL")
                elif not selected_posts:
                    st.warning("No posts selected for deletion")
                elif not st.session_state.connection_status:
                    st.warning("Please test your connection before bulk operations")
                else:
                    # Create progress bar
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    # Get authentication details
                    auth_token = st.session_state.auth_token if auth_method == "JWT/OAuth" else None
                    
                    # Delete posts
                    success_count = 0
                    error_count = 0
                    deleted_ids = []
                    
                    for i, post in enumerate(selected_posts):
                        # Update progress
                        progress = (i + 1) / len(selected_posts)
                        progress_bar.progress(progress)
                        status_text.text(f"Deleting post {i+1} of {len(selected_posts)}")
                        
                        # Delete post
                        result = delete_post(wp_url, post_type, post.get("id"), username, password, auth_token)
                        
                        if result:
                            success_count += 1
                            deleted_ids.append(post.get("id"))
                        else:
                            error_count += 1
                    
                    # Update session state
                    if deleted_ids:
                        st.session_state.posts = [p for p in st.session_state.posts if p.get("id") not in deleted_ids]
                    
                    # Final status
                    st.success(f"Bulk deletion completed: {success_count} successful, {error_count} failed")
        else:
            st.warning("No posts have been fetched. Go to the 'View Posts' tab and fetch posts first")

# Footer
st.markdown("---")
st.markdown("WordPress ACPT Manager Pro - Built with Streamlit")
st.markdown("© 2023 - All rights reserved")
