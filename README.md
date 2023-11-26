# CS3640-A5
## Exploring the Digital Cookie Jar

Objective: Dive deep into the digital world to unravel the intricacies of web cookies. I am on a quest to understand the nuances of first-party and third-party cookies and their varied implementations across diverse website categories like e-commerce, entertainment, and media.

The Tool: Dual-mode Web Crawler
I have engineered a versatile web crawler with two operational modes:

🕸️ Scrape Mode <br>
Purpose: Harvest cookies directly from your chosen websites. <br>
Function: Feed it URLs and it meticulously scrapes cookies from each site.

🔍 Research Mode <br>
Purpose: Simulate a Google search experience. <br>
Function: Input keywords, and it fetches top-ranking websites related to your query.


## Getting started

This project uses ChromeDriver for Selenium testing. The ChromeDriver is automatically installed when you run the project, but you will need to install Chrome if you don't already have it. You can download Chrome [here](https://www.google.com/chrome/).

The crawler creates and uses a database to manage and store data efficiently. To ensure proper functionality, you will need database management software. If you don't already have a preferred method, the easiest to setup is DB Browser for SQLite. You can download it [here](https://sqlitebrowser.org/).


## Running the project

To get the crawler up and running, follow these steps:

1. Clone the repository to your local machine.

2. Open the project in your preferred IDE or terminal.

3. Install the dependencies listed by running the command 'install requirements.txt'.

4. Run 'python crawler.py' to start the crawler.

5. To proceed crawling, use either 'scrape' or 'research' commands as instructed by the help message. Each mode will prompt you for information to start crawling.

6. Check the repository for 'cookies.db' and open it with your database management software to view the data.


## CREDITS

