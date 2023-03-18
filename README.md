# Boook
#### Video Demo:  https://youtu.be/e-dCUES2IkA

#### Description:

Booook is an interactive website that allows users to search, rate and keep track of books they have read, want to read, or currently reading. The website was developed to provide an organized and personalized platform for book enthusiasts to easily discover new books, rate and review their favorite books, and keep track of their reading progress.

- One of the main features of Booook is its user system, which requires users to create an account to access the full functionality of the website. During the registration process, users must fill in several fields including their first name, last name, username, email address, password, and retype password. The user system ensures that all fields are correctly filled in, and it sends an alert message if any of the fields are left blank. Also, usernames and email addresses can only be used once, so users are alerted if they attempt to register with an already existing username or email address.

- The registration process is completed by the system using the pbkdf2_sha256 password hashing algorithm, which guarantees the security of user passwords. Passwords must meet certain requirements, such as being at least 8 characters long and containing at least one uppercase letter and one number. The system also requires users to retype their passwords to confirm the password they entered is correct.

 - Booook's sign-in and session functionality are designed to provide users with a seamless experience. Once logged in, users can navigate through the website without having to sign in repeatedly. During sign-in, the system checks the user's username and password hash to verify their identity.

- The home page of Booook features a search bar and radio buttons that allow users to search for books based on title, author, publisher, and category. Once a search is initiated, the website uses the Google Books API to fetch book data that matches the user's search criteria. This feature helps users discover new books that they might not have found otherwise.

- When a user clicks on a book title, they are directed to the book page where they can rate, delete or update their rating, see the book's average rating, add the book to their library, or remove it from their library. Users can also write and delete their book reviews and read reviews from other users. If they click on the author's name or category, they will be redirected to other books from that author or category.

- The user page provides users with an overview of their reading progress, including how many books they have read, want to read, or currently reading. The user page also displays the number of books they have rated and their personal information.

- The website's database is built using SQLite, a lightweight database engine that offers high performance and reliability. SQLite is ideal for Booook as it can handle the large volume of book data that is stored on the website.

In summary, Booook is an innovative book website that provides users with a personalized platform to search for books, rate and review their favorite books, and keep track of their reading progress. The user system ensures the security of user data, while the home page's search bar and radio buttons help users discover new books easily. The book page provides users with the necessary tools to rate, review and keep track of books, while the user page offers an overview of their reading progress. The SQLite database ensures that the website can handle the large volume of book data stored on the website. Overall, Booook is an ideal platform for book enthusiasts who want to explore new books and keep track of their reading progress.

#### Requirements

- Flask
- Flask-Session
- requests
- sqlite3
- datetime
- Mail
- Message

#### Installation

- Clone the repository:

    ```git clone https://github.com/your-username/booook.git```


- Install the required dependencies:

    ```pip install -r requirements.txt```

- Run the app:

    ```flask run```

- Open a web browser and go to `http://localhost:5000` to view the app.


#### Final project of CS50

This is the final project of CS50 by Harvard Introduction to Computer Science course. You can find my LinkedIn profile at [Tamkin Tamrazli](https://www.linkedin.com/in/tamkintamraz/). If you have any questions or feedback, feel free to contact me.