import os
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
from newsapi import NewsApiClient
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from .state import GraphState
from .tools import NewsApiParams

model = "gpt-4o-mini"
llm = ChatOpenAI(model=model)

def generate_newsapi_params(state: GraphState) -> GraphState:
    """Based on the query, generate News API params."""
    parser = JsonOutputParser(pydantic_object=NewsApiParams)
    yesterday_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    two_days_ago_date = (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d")
    past_searches = state["past_searches"]
    num_searches_remaining = state["num_searches_remaining"]
    news_query = state["news_query"]

    template = """
    The wanted language is Hebrew. 
    The country is Israel.

    Create a param dict for the News API of the most relevant articles in Israel only in the past 24 hours-- 

    from {two_days_ago_date} to {yesterday_date}

    These searches have already been made. Loosen the search terms to get more results.
    {past_searches}
    
    Following these formatting instructions:
    {format_instructions}

    Including this one, you have {num_searches_remaining} searches remaining.
    If this is your last search, use all news sources and a 30 days search range.
    """

    prompt_template = PromptTemplate(
        template=template,
        variables={"yesterday_date": yesterday_date, "two_days_ago_date": two_days_ago_date, "past_searches": past_searches, "num_searches_remaining": num_searches_remaining},
        partial_variables={"format_instructions": parser.get_format_instructions()}
    )

    chain = prompt_template | llm | parser
    result = chain.invoke({"yesterday_date": yesterday_date, "two_days_ago_date": two_days_ago_date, "past_searches": past_searches, "num_searches_remaining": num_searches_remaining})
    state["newsapi_params"] = result
    return state

def retrieve_articles_metadata(state: GraphState) -> GraphState:
    """Using the NewsAPI params, perform api call."""
    newsapi_params = state["newsapi_params"]
    state['num_searches_remaining'] -= 1

    try:
        newsapi = NewsApiClient(api_key=os.getenv('NEWSAPI_KEY'))
        articles = newsapi.get_everything(**newsapi_params)
        state['past_searches'].append(newsapi_params)
        scraped_urls = state["scraped_urls"]

        new_articles = []
        for article in articles['articles']:
            if article['url'] not in scraped_urls and len(state['potential_articles']) + len(new_articles) < 10:
                new_articles.append(article)

        state["articles_metadata"] = new_articles

    except Exception as e:
        print(f"Error: {e}")

    return state

def retrieve_articles_text(state: GraphState) -> GraphState:
    """Web scrapes to retrieve article text."""
    articles_metadata = state["articles_metadata"]
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36'
    }

    potential_articles = []

    for article in articles_metadata:
        url = article['url']
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            text = soup.get_text(strip=True)
            potential_articles.append({
                "title": article["title"], 
                "url": url, 
                "description": article["description"], 
                "text": text
            })
            state["scraped_urls"].append(url)

    state["potential_articles"].extend(potential_articles)
    return state

def select_top_urls(state: GraphState) -> GraphState:
    """Based on the article synopses, choose the top-n articles to summarize."""
    news_query = state["news_query"]
    num_articles_tldr = state["num_articles_tldr"]
    potential_articles = state["potential_articles"]

    formatted_metadata = "\n".join([f"{article['url']}\n{article['description']}\n" for article in potential_articles])

    prompt = f"""
    Based on the user news query:
    {news_query}

    Reply with a list of strings of up to {num_articles_tldr} relevant urls.
    Don't add any urls that are not relevant or aren't listed specifically.
    {formatted_metadata}
    """
    result = llm.invoke(prompt).content
    return state

async def summarize_articles_parallel(state: GraphState) -> GraphState:
    """Summarize selected articles in parallel."""
    # Implementation here
    return state

def format_results(state: GraphState) -> GraphState:
    """Format the results for display."""
    # Implementation here
    return state

def articles_text_decision(state: GraphState) -> str:
    """Decide next action based on article text retrieval."""
    if not state["articles_metadata"]:
        if state["num_searches_remaining"] > 0:
            return "generate_newsapi_params"
        return "format_results"
    return "retrieve_articles_text"
