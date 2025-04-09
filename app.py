print("Starting Flask app...") 
from flask import Flask, render_template, request
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time
import statistics

# app = Flask(__name__)
app = Flask(__name__, template_folder='.')

def scrape_amazon(keyword):
    url = f"https://www.amazon.com/s?k={keyword.replace(' ', '+')}"
    
    # Setup Selenium WebDriver
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # Run in background
    options.add_argument("--disable-blink-features=AutomationControlled")
    service = Service(executable_path="./chromedriver")  # macOS/Linux
    driver = webdriver.Chrome(service=service, options=options)

    
    driver.get(url)
    time.sleep(5)  # Wait for page to load
    
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    driver.quit()
    
    products = []
    for item in soup.select("[data-component-type='s-search-result']")[:22]:  # Limit to 22 items
        # Fixed syntax ⬇️
        brand_element = item.select_one("h5")
        name_element = item.select_one("h2")  # Target the <h2> element
        price_element = item.select_one("span.a-price span")
        rating_element = item.select_one("span.a-icon-alt")
        rating_count_element = item.select_one("span.a-size-base.s-underline-text")
        bought_element = item.select_one("span.a-size-base.a-color-secondary")
        bought_last_month = bought_element.text.strip() if bought_element else "N/A"

        product = {
            'brand': name_element.text.split()[0] if name_element else "N/A",
            'name': name_element.get("aria-label") if name_element else "N/A",
            'price': price_element.text.strip() if price_element else "N/A",
            'rating': rating_element.text.split()[0] if rating_element else "N/A",
            'rating_count': rating_count_element.text.strip() if rating_count_element else "N/A",
            'bought_last_month': bought_last_month
        }
        products.append(product)
    
    return products

def calculate_summary(products):
    valid_prices = []
    valid_ratings = []
    valid_rating_counts = []
    valid_bought = []

    for p in products:
        # Process prices
        if p['price'] != "N/A":
            try:
                price = float(p['price'].replace('$', '').replace(',', ''))
                valid_prices.append(price)
            except ValueError:
                continue

    prices = [float(p['price'].replace('$', '')) for p in products if p['price'] != "N/A"]
    ratings = [float(p['rating']) for p in products if p['rating'] != "N/A"]
    rating_counts = [int(p['rating_count'].replace(',', '')) for p in products if p['rating_count'] != "N/A"]
    
    return {
        'average_price': round(statistics.mean(valid_prices), 2) if valid_prices else "N/A",
        'highest_price': max(valid_prices) if valid_prices else "N/A",  # New field
        'lowest_price': min(valid_prices) if valid_prices else "N/A",   # New field
        'average_rating_count': round(statistics.mean(rating_counts)) if rating_counts else "N/A",
        'highest_rating': max(ratings) if ratings else "N/A",
        'lowest_rating': min(ratings) if ratings else "N/A",
        'highest_bought': "N/A",  # Data unavailable
        'lowest_bought': "N/A"
    }

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        keyword = request.form.get("keyword")
        products = scrape_amazon(keyword)
        
        # Sort by rating_count descending (handle "N/A" as 0)
        products_sorted = sorted(
            products,
            key=lambda x: (
                int(x['rating_count'].replace(',', '')) 
                if x['rating_count'] != "N/A" 
                else 0
            ),
            reverse=True
        )
        
        summary = calculate_summary(products_sorted)
        return render_template("results.html", products=products_sorted, summary=summary)
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)