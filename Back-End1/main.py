from website import create_app

# main.py - Entry point of our Flask application

# Creating an instance of our Flask application using the create_app function
app = create_app()  

if __name__ == "__main__":
    app.run(debug=False)   # Turn this False to stop debugging