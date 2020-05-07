import csv
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
engine = create_engine('postgres://ukupjdcvgqjvns:603d9f6a1b963ec811d4830f5010fee6d95a648723e413e1b3a46879e1e3873e@ec2-18-215-99-63.compute-1.amazonaws.com:5432/ddkla0uuj9hnb')
db = scoped_session(sessionmaker(bind=engine))
def main():
    b = open("books.csv")
    reader = csv.reader(b)
    for isbn,title,author,year in reader:
        db.execute("INSERT INTO books (isbn, title, author, year) VALUES (:isbn, :title, :author, :year)",
        {"isbn": isbn, "title":title , "author": author, "year":year}) # substitute values from CSV line into SQL comm # loop gives each column a name
    print("Added")
    db.commit()

if __name__=="__main__":
    main()
