import requests
import subprocess
import json
import re
import concurrent.futures
from difflib import SequenceMatcher
import os
import sys
from bs4 import BeautifulSoup as Soup
from playwright.sync_api import sync_playwright
from playwright.async_api import async_playwright, TimeoutError

similarity=0.6
flag=sys.argv[1]
path=os.getcwd()

def process_line(line, author):
    # Process each line for searching and downloading books
    book_search = Booksearch(title=line, language="eng", filetype=sys.argv[3])
    result = book_search.search()
    if result:
        extensions = result["extensions"]
        mirrors = result["mirrors"]
        table_data = result["table_data"]
        file_details = book_search.give_result(extensions, table_data, mirrors, None)
        if file_details:
            book_search.cursor(file_details["url"], "C:/Users/Nikola/Documents/BookScraper", file_details["file"])

def process_line2(line, author):
    # Process each line for searching and downloading books
    book_search = Booksearch(title=line, language="eng")
    result = book_search.search()
    if result:
        extensions = result["extensions"]
        mirrors = result["mirrors"]
        table_data = result["table_data"]
        file_details = book_search.give_result(extensions, table_data, mirrors, None)
        if file_details:
            book_search.cursor(file_details["url"], "C:/Users/Nikola/Documents/BookScraper", file_details["file"])


def run_parallel(ath):
    Lines = file_list(f"C:/Users/Nikola/Documents/BookScraper/{ath}_bibliography.txt")
    if(ath==author):
    # Use ThreadPoolExecutor to run in parallel
        with concurrent.futures.ThreadPoolExecutor() as executor:
        # Map the process_line function to each line (book title) concurrently
            futures = [executor.submit(process_line, line, author) for line in Lines]

        # Ensure all futures are completed
            for future in concurrent.futures.as_completed(futures):
                try:
                    future.result()  # Check if any exception occurred
                except Exception as e:
                    print(f"Error processing line: {e}")
    else:
        print("Gubavac.")
        with concurrent.futures.ThreadPoolExecutor() as executor:
        # Map the process_line function to each line (book title) concurrently
            futures = [executor.submit(process_line2, line, author) for line in Lines]

        # Ensure all futures are completed
            for future in concurrent.futures.as_completed(futures):
                try:
                    future.result()  # Check if any exception occurred
                except Exception as e:
                    print(f"Error processing line: {e}")


def main_autor(author, similarity):
    # returns all the books writen by an author from openlibrary
    # using similarity for filtering the results
    status = True 
    if status is not False:
        search_url = "http://openlibrary.org/search.json?author=" + author
        jason = requests.get(search_url)
        jason = jason.text
        data = json.loads(jason)
        data = data["docs"]
        if data != []:
            metr = 0
            books = []
            for i in range(0, len(data) - 1):
                title = data[metr]["title"]
                metr = metr + 1
                books.append(title)
                mylist = list(dict.fromkeys(books))

            #       Filtrering results: trying to erase similar titles
            words = [
                " the ",
                "The ",
                " THE ",
                " The" " a ",
                " A ",
                " and ",
                " of ",
                " from ",
                "on",
                "The",
                "in",
            ]

            noise_re = re.compile(
                "\\b(%s)\\W" % ("|".join(map(re.escape, words))), re.I
            )
            clean_mylist = [noise_re.sub("", p) for p in mylist]
            
            for i in clean_mylist:
                for j in clean_mylist:
                    a = similar(i, j, similarity)
                    if a is True:
                        clean_mylist.pop(a)

            clean_mylist.sort()
            print(" ~Books found to OpenLibrary Database:\n")
            for i in clean_mylist:
                print(i)
            return clean_mylist
        else:
            print("(!) No valid author name, or bad internet connection.")
            print("Please try again!")
            return None


def similar(a, b, similarity):
    """function which check similarity between two strings"""
    ratio = SequenceMatcher(None, a, b).ratio()
    if ratio > similarity and ratio < 1:
        return True
    else:
        return False


def save_to_txt(lista, path, author):
    # save the books list to txt file.
    name = f"{author}_bibliography.txt"
    full_path = os.path.join(path, name)
    
    # Check if the file exists, if yes, delete it
      # delete the existing file
    
    # Open the file in append mode and write the content
    with open(full_path, "a", encoding="utf-8") as f1:
        for content in lista:
            f1.write(content + " " + author + os.linesep)
    
    print("\nList saved at: ", full_path, "\n")

class Booksearch:
    """Searching LibGen and returning book details and mirror links."""

    def __init__(self, title, author=None, language="eng", filetype=None, libgenurl="http://libgen.gs"): #li gs vg pm
        self.title = title
        self.author = author
        self.language = language
        self.filetype = filetype
        self.mirror = None
        self.libgenurl = libgenurl
        self.session = requests.Session()  # Ensure this line initializes the session
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0"
        })


    def search(self):
      with sync_playwright() as p:
        # Launch the browser (use Brave if needed)
        browser = p.chromium.launch(headless=True, args=["--disable-web-security", "--allow-insecure-localhost"])
          # Set headless=True to run without UI
        page = browser.new_page()

        # Navigate to LibGen
        try:
            page.goto(self.libgenurl + "/index.php")
        except TimeoutError:
            print("Page not accessible.")
            return None
        
        # Wait for the input field to be visible
        page.wait_for_selector("input[name='req']")

        # Fill the search form
        if (self.language==None and self.filetype==None):
            page.fill("input[name='req']", f"{self.title}" ) #" lang:eng + ext:pdf"
        elif (self.language!=None and self.filetype==None):
            page.fill("input[name='req']", f"{self.title}" +" lang:"+f"{self.language}")
        elif (self.language==None and self.filetype!=None):
            page.fill("input[name='req']", f"{self.title}" +" ext:"+f"{self.filetype}")
        elif (self.language!=None and self.filetype!=None):
            page.fill("input[name='req']", f"{self.title}"+" lang:"+f"{self.language}" +" ext:"+f"{self.filetype}")
        page.wait_for_selector("#gmode+ .custom-control-label strong", state='visible')
        page.click("#gmode+ .custom-control-label strong")
        # Wait for the submit button to be enabled and visible before clicking
        page.wait_for_selector("button#button-addon2", state='visible')
        
        # Click the submit button
        page.click("button#button-addon2")

        # Wait for the results to load
        #Brisanje knjiga i pisanje koje nisu skinut za manual check
        try:
            page.wait_for_selector("table#tablelibgen", timeout=5000)
        except TimeoutError:
            print("Bad book name.")
            with open(os.path.join(path, f"{author}m_bibliography.txt"), "a", encoding="utf-8") as f1:
                f1.write(self.title + "\n")
            return None

        # Get the content of the page
        content = page.content()
        browser.close()

        # Parse the response HTML
        soup = Soup(content, "html.parser")
        links_table = soup.find("table", {"class": "table table-striped", "id": "tablelibgen"})
        if not links_table:
            print("Error: Couldn't find the expected table in the HTML.")
            return None

        table_data = []
        mirrors = []
        extensions = []

        # Parse the rows in the table
        for row in links_table.find_all("tr")[1:]:  # Skip the header row
            cols = row.find_all("td")
            if len(cols) >= 9:
                try:
                    # Extract the mirror link from the last column
                    mirror_link = cols[-1].find("a", href=True)["href"]
                    if not mirror_link.startswith("https"):
                        mirror_link = self.libgenurl + mirror_link
                    mirrors.append(mirror_link)

                    # Collect table data
                    row_data = [col.text.strip() for col in cols]
                    table_data.append(row_data)

                    # Get file extension (column 8 or fallback if unavailable)
                    extensions.append(cols[8].text.strip() if len(cols) > 8 else "Unknown")
                except Exception as e:
                    print(f"Error processing row: {e}")
                    continue
            else:
                print(f"Skipping row due to insufficient columns: {len(cols)} columns found")

        # Store details in a dictionary
        table_details = {
            "extensions": extensions,
            "table_data": table_data,
            "mirrors": mirrors
        }

        return table_details


    def give_result(self, extensions, table_data, mirrors, filetype=None):
        """Return the result based on the filetype."""
        try:
            if filetype is not None:
                # Look for the specific file type in the extensions
                for idx, ext in enumerate(extensions):
                    if filetype == ext:
                        result = {
                            "url": mirrors[idx],
                            "file": extensions[idx]
                        }
                        print("\nDownloading Link: FOUND")
                        return result
            else:
                # Return the first result by default
                result = {
                    "url": mirrors[0],
                    "file": extensions[0]
                }
                print("\nDownloading Link: FOUND")
                return result
        except IndexError:
            print("Downloading Link: NOT FOUND\n")
            print("================================")
            return None

    def cursor(self, mirror_url, destination, filename, force=False):
        """Navigate to the download page and save the download link."""
        file_path = os.path.join(destination, filename)

        # Skip if the file already exists and force is not True
        if os.path.exists(file_path) and not force:
            print(f"File {filename} already exists. Skipping download.")
            return

        print(f"Navigating to {mirror_url} to get download link for {self.title}...")

        with sync_playwright() as p:
            # Launch the browser with desired arguments
            browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-web-security"])
            context = browser.new_context(bypass_csp=True)
            page = context.new_page()

            try:
                page.goto(mirror_url)

                # Wait for the GET link to be present
                get_button_selector = 'a[href*="get.php"]'
                page.wait_for_selector(get_button_selector, state="visible")

                # Extract the GET link directly
                get_link = page.query_selector(get_button_selector).get_attribute('href')

                if get_link:
                    download_url = self.libgenurl + "/" + get_link  # Ensure the full URL is correct
                    print(f"Saving download link: {download_url}")

                    # Save the download link to a text file
                    with open("download_links.txt", "a") as link_file:
                        link_file.write(f"{download_url}\n")

                    print(f"Download link saved for: {self.title}")
                else:
                    print("GET link not found.")

            except Exception as e:
                print(f"Failed to retrieve GET link: {e}")

            finally:
                context.close()
                browser.close()

def file_list(file):
    """checks if the input file is a .txt file and adds each separate line
    as a book to the list 'Lines'.
    After return this list to download_from_txt
    """
    if file.endswith(".txt"):
        try:
            file1 = open(file, "r", encoding="utf-8")
            Lines = file1.readlines()
            for i in Lines:
                if i == "\n":
                    Lines.remove(i)
            
            return Lines
        except FileNotFoundError:
            print("Error:No such file or directory:", file)
    else:
        print("\nError:Not correct file type. Please insert a '.txt' file")


def libgen_book_find(title, author, publisher, destination, filetype, force, libgenurl):
    """Searching @ LibGen for a single book."""
    try:
        book_search = Booksearch(title, author, publisher, filetype, libgenurl)
        result = book_search.search()

        # Check if the result is valid
        if result is None:
            print("No results found for the search.")
            return

        extensions = result["extensions"]  # Extract extensions from the search result
        tb = result["table_data"]           # Extract table data
        mirrors = result["mirrors"]         # Extract mirrors

        # Call give_result with all required arguments
        file_details = book_search.give_result(extensions, tb, mirrors, filetype)

        if file_details is not None:
            book_search.cursor(file_details["url"], destination, file_details["file"], force)
    except TypeError as e:
        print(f"Error occurred: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    match flag:
        #cleaning directoryyyyyyyyyyyyyyyyyyyyyyyyyyyyyy
        case "c":
            for file in os.listdir(path):
                if file.endswith(".txt"):
                    os.remove(file)
            print("Clean!\n")
        ##single booooksssssssssssssssssssssssssssssss
        case "s":
            author=sys.argv[2]
            print("Single book!\n")
            book_search = Booksearch(title=sys.argv[2], )
            result = book_search.search()
            if result:
                extensions = result["extensions"]
                mirrors = result["mirrors"]
                table_data = result["table_data"]
                file_details = book_search.give_result(extensions, table_data, mirrors, None)
                if file_details:
                    book_search.cursor(file_details["url"], "C:/Users/Nikola/Documents/BookScraper", file_details["file"])
            if os.path.exists(os.path.join(path, f"{author}_bibliography_missing.txt")):
                os.remove(os.path.join(path, f"{author}_bibliography_missing.txt"))
            newpath = "C:/Users/Nikola/Documents/BookScraper"+"/downloads/"+f"{author}"
            args = ['aria2c.exe','--input-file=' + os.path.join(path, "download_links.txt")]
            subprocess.run(args)
        case "sl":
            author=sys.argv[2]
            print("Single book!\n")
            book_search = Booksearch(title=sys.argv[2], language=sys.argv[3])
            result = book_search.search()
            if result:
                extensions = result["extensions"]
                mirrors = result["mirrors"]
                table_data = result["table_data"]
                file_details = book_search.give_result(extensions, table_data, mirrors, None)
                if file_details:
                    book_search.cursor(file_details["url"], "C:/Users/Nikola/Documents/BookScraper", file_details["file"])
            if os.path.exists(os.path.join(path, f"{author}_bibliography_missing.txt")):
                os.remove(os.path.join(path, f"{author}_bibliography_missing.txt"))
            newpath = "C:/Users/Nikola/Documents/BookScraper"+"/downloads/"+f"{author}"
            args = ['aria2c.exe','--input-file=' + os.path.join(path, "download_links.txt")]
            subprocess.run(args)
        case "sle":
            author=sys.argv[2]
            print("Single book!\n")
            book_search = Booksearch(title=sys.argv[2], language=sys.argv[3], filetype=sys.argv[4])
            result = book_search.search()
            if result:
                extensions = result["extensions"]
                mirrors = result["mirrors"]
                table_data = result["table_data"]
                file_details = book_search.give_result(extensions, table_data, mirrors, None)
                if file_details:
                    book_search.cursor(file_details["url"], "C:/Users/Nikola/Documents/BookScraper", file_details["file"])
            if os.path.exists(os.path.join(path, f"{author}_bibliography_missing.txt")):
                os.remove(os.path.join(path, f"{author}_bibliography_missing.txt"))
            newpath = "C:/Users/Nikola/Documents/BookScraper"+"/downloads/"+f"{author}"
            args = ['aria2c.exe', '--input-file=' + os.path.join(path, "download_links.txt")]
            subprocess.run(args)
        case "se":
            author=sys.argv[2]
            print("Single book!\n")
            book_search = Booksearch(title=sys.argv[2], filetype=sys.argv[3])
            result = book_search.search()
            if result:
                extensions = result["extensions"]
                mirrors = result["mirrors"]
                table_data = result["table_data"]
                file_details = book_search.give_result(extensions, table_data, mirrors, None)
                if file_details:
                    book_search.cursor(file_details["url"], "C:/Users/Nikola/Documents/BookScraper", file_details["file"])
            if os.path.exists(os.path.join(path, f"{author}_bibliography_missing.txt")):
                os.remove(os.path.join(path, f"{author}_bibliography_missing.txt"))
            newpath = "C:/Users/Nikola/Documents/BookScraper"+"/downloads/"+f"{author}"
            args = ['aria2c.exe','--input-file=' + os.path.join(path, "download_links.txt")]
            subprocess.run(args)
        #bibliographyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy
        case "b":
            author=sys.argv[2]
            for file in os.listdir(path):
                if file.endswith(".txt"):
                    os.remove(file)
            print("Clean!\n")
            print("Bibliography!\n")
            save_to_txt(main_autor(author, similarity), path, author)
            run_parallel(author)
            if(os.path.isfile(os.path.join(path, "download_links.txt"))):
                newpath = "C:/Users/Nikola/Documents/BookScraper"+"/downloads/"+f"{author}" 
                if not os.path.exists(newpath):
                    os.makedirs(newpath)
                args = ['aria2c.exe', '--max-concurrent-downloads=1', '--max-connection-per-server=8','--max-tries=4','--retry-wait=3','--timeout=5','--human-readable=true','--download-result=full','--file-allocation=none', '--input-file=' + os.path.join(path, "download_links.txt"), '--dir='+ newpath]
                subprocess.run(args)
            if(os.path.isfile(os.path.join(path, "download_links.txt"))):
                os.remove(os.path.join(path, "download_links.txt"))
            run_parallel(author+"m")
            if(os.path.isfile(os.path.join(path, "download_links.txt"))):
                newpath = "C:/Users/Nikola/Documents/BookScraper"+"/downloads/"+f"{author}m" 
                if not os.path.exists(newpath):
                    os.makedirs(newpath)
                args = ['aria2c.exe', '--max-concurrent-downloads=1', '--max-connection-per-server=8','--max-tries=4','--retry-wait=3','--timeout=5','--human-readable=true','--download-result=full','--file-allocation=none', '--input-file=' + os.path.join(path, "download_links.txt"), '--dir='+ newpath]
                subprocess.run(args)
            
        case _:
            print("Invalid input.")