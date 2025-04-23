import asyncio
import os
from dotenv import load_dotenv
from agent.agent import app
from langgraph.graph import Graph

async def start_graph_flow(app: Graph, query: str, num_searches_remaining: int = 10, num_articles_tldr: int = 3):
    """Start the graph workflow."""
    initial_state = {
        "news_query": query,
        "num_searches_remaining": num_searches_remaining,
        "newsapi_params": {},
        "past_searches": [],
        "articles_metadata": [],
        "scraped_urls": [],
        "num_articles_tldr": num_articles_tldr,
        "potential_articles": [],
        "tldr_articles": [],
        "formatted_results": ""
    }
    
    result = await app.ainvoke(initial_state)
    return result["formatted_results"]



async def run_workflow():
    # Load environment variables
    load_dotenv()
    
    # Check for required environment variables
    required_vars = ['NEWSAPI_KEY', 'OPENAI_API_KEY']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

    try:
        # Create and run the graph
        query = "what are the top news about israel?"
        result = await start_graph_flow(app, query, num_articles_tldr=3)
        print(result)
    except Exception as e:
        print(f"Error running workflow: {str(e)}")
        raise

if __name__ == "__main__":
    try:
        asyncio.run(run_workflow())
    except KeyboardInterrupt:
        print("\nWorkflow interrupted by user")
    except Exception as e:
        print(f"Fatal error: {str(e)}")