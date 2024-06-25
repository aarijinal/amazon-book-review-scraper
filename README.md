## Acquisition and Preprocessing of Book Data

### <u>Introduction</u>
This project utilizes web scraping to collect data from amazon.com on best selling books.  The web_scraper.py script cycles through books and creates two directories- one directory containing a parent table that has book information and another directory hosting child tables with review data for each book in the parent table. The parent table  has the following features:
- **ID** - The book ID 
- **Title** -  The title of the book
- **Authors** - The author of the book
- **Price** - The selling cost of the book on amazon.com
- **Ratings** - The total star rating (out of 5)  of the book
- **Num_reviews** - The number of ratings that contributed to the final rating of the book

The child tables have the following features:
- **ID** - number of review in queue
- **Book_ID** - ID corresponding to the book ID in the parent table
- **Title** - title given to review by the reviewer
- **Location** - location of the reviewer
- **Reviewed_on** - date the review was written
- **Rating** - number of stars (out of 5) the reviewer assigned to the book
- **Body** - content of the review
- **Num_helpful_votes** - the number of people who found the review helpful 

The final dataset hosts a parent table limited to 200 books and review tables with a max of 500 reviews for each book. 

### How To Use It
```sh
python3 web_scraper.py -nb 200 -nr 500
```
The arguments `-nb` and `-nr` (currently default to 200 and 500 respectively) can be specified to collect a larger sample of books and reviews.

**Requirements**

The script is run using Python3 and requires the installation of the selenium and webdriver_manager python packages. Both packages can be installed using pip install in the command line.  

**Challenges/Limitations**

*Captchas*:  The speed at which the scraper cycles through page links could trigger amazon to issue a captcha to test if a bot is on the page.  
 
*Time*: The script currently takes 4 hours to run, collecting 200 books and 500 reviews for each book. Any increase in the numbers collected will result in an increase in the runtime of the code.
  
*Inconsistent HTML*: HTML tags representing similar elements change across pages 
