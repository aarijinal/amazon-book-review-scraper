import re
import csv
import os
import time

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService

from webdriver_manager.chrome import ChromeDriverManager

class WebCrawler:
    '''Base Class for a web crawler'''

    def __init__(self, url, driver):
        self.url = url
        self.driver = driver
        self.driver.get(self.url)

    def wait(self, seconds=5):
        '''Wait for the specified amount of time'''

        self.driver.implicitly_wait(seconds)

    def wait_until(self, until):
        '''Waits a set amount of time for a web driver until event'''

        WebDriverWait(self.driver, 10).until(until)

    def go_to_next_book_page(self):
        pass

    def click_link(self, link_el, open_in_new_tab=False):
        '''Opens a link in a new tab or in the same tab'''
        if open_in_new_tab:
            link_el.send_keys(Keys.COMMAND + Keys.RETURN)
        else:
            link_el.click()
    
    def quit(self):
        '''Ends the session for the crawler'''
        self.driver.quit()


class AmazonBooksWebCrawler(WebCrawler):
    # used to generate IDs for the scraped books so we can tie them to their reviews
    next_book_id = 1

    # used to generate IDs for the scraped reviews
    next_review_id = 1

    def __init__(self, driver):
        url = "https://www.amazon.com/s?k=best+seller+books+2022&i=stripbooks&sprefix=best%2Cstripbooks%2C69&ref=nb_sb_ss_ts-doa-p_1_4"
        super().__init__(url, driver)


    def has_next_book_page(self):
        '''Checks if there is a next page'''
        try:
            next_button = self.driver.find_element(By.CSS_SELECTOR, "a.s-pagination-next")
            # if we find the disabled class in the next button's list of classes
            # then there is no next page
            is_disabled = 's-pagination-disabled' in next_button.get_attribute("class").split()
            return not is_disabled
        except NoSuchElementException:
            # if we don't find the next button there is no next page
            return False


    def has_next_review_page(self):
        '''Checks if there is a next page of reviews'''
        try:
            next_button = self.driver.find_element(By.CSS_SELECTOR, "ul.a-pagination > li.a-last > a")

            # if we find the disabled class in the next button's list of classes
            # then there is no next page
            is_disabled = 'a-disabled' in next_button.get_attribute("class").split()
            return not is_disabled
        except NoSuchElementException:
            # if we don't find the next button there is no next page
            return False


    def go_to_next_book_page(self):
        '''Moves to the next page if possible'''
        try:
            # find the next button
            next_button = self.driver.find_element(By.CSS_SELECTOR, "a.s-pagination-next")

            # if the next button is not disabled then click it to navigate to the next page
            is_disabled = 's-pagination-disabled' in next_button.get_attribute("class").split()
            if not is_disabled:
                next_button.click()
                return True
            else:
                return False
        except Exception as e:
            # handle any errors that might occur so the program doesn't stop
            print("Something went wrong while navigating to the next page", e)
            return False


    def go_to_next_review_page(self):
        '''Moves to the next page of reviews if possible'''
        try:
            # find the next button
            next_button = self.driver.find_element(By.CSS_SELECTOR, "ul.a-pagination > li.a-last > a")

            # if the next button is not disabled then click it to navigate to the next page
            is_disabled = 'a-disabled' in next_button.get_attribute("class").split()
            if not is_disabled:
                next_button.click()
                return True
            else:
                return False
        except Exception as e:
            # handle any errors that might occur so the program doesn't stop
            print("Something went wrong while navigating to the next page", e)
            return False
    

    def scroll_to_bottom(self):
        '''Scrolls to the bottom of the page. Useful to load all the elements in case of lazy-loading'''
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")


    def get_books_and_reviews(self, max_num_books=100, max_num_reviews=1000):
        '''Scrapes the books from the page'''
        try:
            books = []
            book_reviews = {}
            # wait until the book elements are visible
            self.wait_until(EC.visibility_of_all_elements_located((By.CSS_SELECTOR, ".sg-col-inner > .s-widget-container")))
            
            # find all book elements on the page
            book_elements = self.driver.find_elements(By.CSS_SELECTOR, ".sg-col-inner > .s-widget-container")
            for el in book_elements:
                try:
                    # try to extract the title and author information
                    title_authors_el = el.find_element(By.CLASS_NAME, "s-title-instructions-style")

                    # the title and author are usually separated by a new line so we can split to get each one
                    title_authors = title_authors_el.text.split('\n')

                    # sometimes the additional metadata comes before the title and author also separated by newlines
                    # but the title and author are always the last two lines so we retrieve them from the end of the list
                    title = title_authors[-2].strip()

                    # author information can usually be found after the word "by" or after "Book x of x" so we split
                    # the author line and take the last part to get the author information
                    authors = re.split(r'by|Book \d+ of \d+:', title_authors[-1])[1].strip()
                except NoSuchElementException:
                    # if we can't find author or title information for some reason then we default them to empty strings
                    print("Could not find authors and title")
                    title = ""
                    authors = ""

                try:
                    # try to extract the price information
                    price_el = el.find_element(By.CSS_SELECTOR, "span.a-price > span.a-offscreen").get_attribute("innerHTML")

                    # do some preprocessing to get it as a float
                    price = float(price_el.replace("$", ""))
                except NoSuchElementException:
                    # if we fail to find price information then we default it as None. We don't use 0.0 because some books
                    # are actually priced at 0.0 and we want to represent the absence of an entry.
                    print("Could not find pricing information")
                    price = None

                try:
                    # try to extract the ratings information. This rating represents the number of stars a book has been given.
                    ratings_el = el.find_element(By.CSS_SELECTOR, "span.a-icon-alt")

                    # do some preprocessing to get the number of stars a float
                    ratings = float(ratings_el.get_attribute("innerHTML").split(" ")[0])
                except NoSuchElementException:
                    # if we fail to find ratings then default it as None instead of 0.0 to represent the absence of an
                    # entry
                    print("Could not find ratings information")
                    ratings = None

                try:
                    # try to extract the number of reviews
                    num_reviews_el = el.find_element(By.CSS_SELECTOR, "div.s-title-instructions-style + div.a-section > div.a-row > span:nth-child(2)")
                    
                    # do some preprocessing to get the number of reviews as an integer
                    num_reviews = int(num_reviews_el.text.replace(",", ""))

                    # find the url that takes us to the reviews section for the current book
                    reviews_url_el = num_reviews_el.find_element(By.CSS_SELECTOR, "a")
                    
                    print(f"Getting reviews for book {AmazonBooksWebCrawler.next_book_id}: {title}")

                    # if the book has reviews we want to scrape them as well
                    if reviews_url_el:
                        print("Found reviews url: ", reviews_url_el.get_attribute('href'))
                        # open reviews in a new tab
                        self.click_link(reviews_url_el, open_in_new_tab=True)
                        print("Opened in new tab...")

                        # switch to the new tab
                        self.driver.switch_to.window(self.driver.window_handles[1])
                        print("Switched to new tab...")

                        # scroll to the bottom of the page just in case there is lazy loaded content
                        self.scroll_to_bottom()

                        # get all the reviews on the current page
                        reviews = self.get_book_reviews(AmazonBooksWebCrawler.next_book_id, max_num_reviews, initial_page=True)
                        while self.has_next_review_page() and len(reviews) < max_num_reviews:
                            # while there is still another page of reviews and we haven't hit our limit yet...
                            print("Getting the next page of reviews...")

                            # navigate to the next review page
                            self.go_to_next_review_page()

                            # we wait for the page to load and also to limit the rate at which we access the data
                            # if we go too fast amazon might try to have us complete a captcha.
                            time.sleep(3)

                            # scroll to the bottom again to make sure any lazy loaded content is definitely loaded in
                            self.scroll_to_bottom()

                            # grab all the reveiws and append it to the ongoing list for this book
                            reviews += self.get_book_reviews(AmazonBooksWebCrawler.next_book_id, max_num_reviews, initial_page=False)

                        # save the book reviews related to the book
                        book_reviews[AmazonBooksWebCrawler.next_book_id] = reviews

                        # close the reviews tab
                        self.driver.close()

                        # go back to the page of books
                        self.driver.switch_to.window(self.driver.window_handles[0])
                    else:
                        print("No reviews for this book. Skipping...")
                      
                except NoSuchElementException:
                    # if we fail to find any reviews then default as None to represent the absence of an entry
                    print("Could not find number of reviews")
                    num_reviews = None
                
                book = {
                    "id": AmazonBooksWebCrawler.next_book_id,
                    "title": title,
                    "authors": authors,
                    "price": price,
                    "ratings": ratings,
                    "num_reviews": num_reviews,
                }
                books.append(book)
                AmazonBooksWebCrawler.next_book_id += 1
                if len(books) >= max_num_books:
                    # if we have met or are over our quota then stop
                    break
        except NoSuchElementException as e:
            print("Could not find any books: ", e)
        except Exception as e:
            print("Something went wrong while getting books: ", e)
        finally:
            return books, book_reviews


    def get_book_reviews(self, book_id, max_num_reviews, initial_page=False):
        '''Clicks on the review element and scrapes the reviews'''
        try:
            reviews = []
            if initial_page:
                # on the first page when getting reviews there is a "see all reviews" link. we wait for it and click it to access all the reviews
                self.wait_until(EC.visibility_of_all_elements_located((By.CSS_SELECTOR, "div#cr-pagination-footer-0 > a, div#reviews-medley-footer > div.a-row > a")))
                all_reviews_link = self.driver.find_element(By.CSS_SELECTOR, "div#cr-pagination-footer-0 > a, div#reviews-medley-footer > div.a-row > a")
                print("Looking at all reviews...")
                all_reviews_link.click()
            
            # wait for the reviews to become visible
            self.wait_until(EC.visibility_of_all_elements_located((By.CSS_SELECTOR, "div.a-section.review")))
            print("Reviews are visible...")

            # once visible, find all of the reviews on the page
            review_elements = self.driver.find_elements(By.CSS_SELECTOR, "div.a-section.review")
            for el in review_elements:
                try:
                    # try to extract the title
                    print("Getting review title...")
                    title_el = el.find_element(By.CSS_SELECTOR, "a.review-title")
                    title = title_el.text
                except NoSuchElementException:
                    # if we fail to find the title, then default to an empty string
                    print("Could not find review title")
                    title = ""
                
                try:
                    # try to extract the date and location of the review
                    print("Getting review date and location...")
                    date_and_location_el = el.find_element(By.CSS_SELECTOR, "span.review-date")
                    date_and_location = date_and_location_el.get_attribute("innerHTML")

                    # date and location is usually separated by the word "on" so we split on that
                    location, date = date_and_location.split("on")

                    date = date.strip()

                    # in the string containing the location, the first 15 characters is irrelevant
                    # so we take the portion of the string after that
                    location = location[16:].strip()
                except NoSuchElementException:
                    # if we fail to find the data and location, we default the values to empty strings
                    print("Could not find review date and location")
                    date = ""
                    location = ""
                
                try:
                    # try to extract the review rating
                    print("Getting review rating...")
                    rating_el = el.find_element(By.CSS_SELECTOR, "span.a-icon-alt")

                    # do some preprocessing to get the rating as a float
                    rating = float(rating_el.get_attribute("innerHTML").split(" ")[0])
                except NoSuchElementException:
                    # if we fail to find the rating then default it as None to show the absence of an entry
                    print("Could not find review rating")
                    rating = None

                try:
                    # try to extract the body of the review
                    print("Getting review body...")
                    body_el = el.find_element(By.CSS_SELECTOR, "span.review-text-content > span")
                    body = body_el.get_attribute("innerHTML")
                except NoSuchElementException:
                    # if we fail to find the review body then default it as an empty string 
                    print("Could not find review body")
                    body = ""

                try:
                    # try to extract the number of helpful votes
                    print("Getting review helpful votes count...")
                    num_helpful_votes_el = el.find_element(By.CSS_SELECTOR, "span.cr-vote-text")
                    num_helpful_votes = num_helpful_votes_el.text.split(" ")[0]
                    
                    # when there is only one vote Amazon uses the word "One" and when there is more
                    # than one Amazon uses actual digits so we handle the two cases here
                    if num_helpful_votes == "One":
                        num_helpful_votes = 1
                    else:
                        num_helpful_votes = int(num_helpful_votes.replace(",", ""))
                except NoSuchElementException:
                    # if we fail to find the number of helpful votes then default it as None to show
                    # the absence of a value
                    print("Could not find review helpful votes")
                    num_helpful_votes = None

                review = {
                    "id": AmazonBooksWebCrawler.next_review_id,
                    "book_id": book_id,
                    "title": title,
                    "location": location,
                    "reviewed_on": date,
                    "rating": rating,
                    "body": body,
                    "num_helpful_votes": num_helpful_votes
                }
                reviews.append(review)
                AmazonBooksWebCrawler.next_review_id += 1
                if len(reviews) >= max_num_reviews:
                    # if we've reached or surpassed our limit of reviews to retrieve then we can stop
                    break
        except NoSuchElementException as e:
            print("Could not find any reviews: ", e)
        except Exception as e:
            print("Something went wrong while getting reviews: ", e)
        finally:
            return reviews


if __name__ == '__main__':
    # taken from selenium documentation. Basically sets up the browser engine automatically for you
    service = ChromeService(executable_path=ChromeDriverManager().install())

    options = Options()
    # uncomment the line below to run the crawler without opening a browser application on your computer
    # options.add_argument("--headless")
    driver = webdriver.Chrome(service=service, options=options)

    crawler = AmazonBooksWebCrawler(driver)

    # create directories for the books and reviews
    books_dir = os.path.join(os.getcwd(), "books")
    if not os.path.exists(books_dir):
        os.mkdir(books_dir)

    reviews_dir = os.path.join(os.getcwd(), "reviews")
    if not os.path.exists(reviews_dir):
        os.mkdir(reviews_dir)

    max_num_books = 200
    max_num_reviews = 500

    books, book_reviews = crawler.get_books_and_reviews(max_num_books, max_num_reviews)
    while crawler.has_next_book_page() and len(books) < max_num_books:
        # while books remain and we haven't hit our quota...

        # navigate tot he next page of books
        crawler.go_to_next_book_page()

        print("Going to next page...")

        # wait for the page to load and also slow down so Amazon doesn't
        # make us solve a captcha
        time.sleep(3)

        # scroll to the bottom of the page to make sure everything is lazy loaded in
        crawler.scroll_to_bottom()

        # get all the books and reviews from the page
        page_books, page_book_reviews = crawler.get_books_and_reviews(max_num_books, max_num_reviews)

        # add to the collection of books and reviews already retrieved
        books += page_books
        book_reviews |= page_book_reviews # merge the dictionaries

    # write the books and reviews to files
    print("Writing books to file...")
    with open(f'{books_dir}/books.csv', 'w') as books_csv:  
        writer = csv.writer(books_csv)
        header = books[0].keys()
        writer.writerow(header)
        for book in books:
            writer.writerow(book.values())

    for book in books:
        try:
            reviews = book_reviews[book["id"]]
        
            if reviews:
                print("Writing reviews to file...")
                with open(f'{reviews_dir}/book_{book["id"]}_reviews.csv', 'w') as reviews_csv:
                    writer = csv.writer(reviews_csv)
                    header = reviews[0].keys()
                    writer.writerow(header)
                    for review in reviews:
                        writer.writerow(review.values())
        except Exception as e:
            print("Something went wrong while writing reviews", e)
            print("Trying next book's reviews...")
            continue

    crawler.quit()
