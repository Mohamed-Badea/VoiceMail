import socket  # Importing socket module to handle network connections
import mysql.connector  # Importing mysql.connector to interact with MySQL database
import tkinter as tk  # Importing tkinter for building the GUI
from tkinter import messagebox  # Importing messagebox to show popup messages
import pyaudio  # Importing pyaudio for handling audio recording
import wave  # Importing wave to work with .wav audio files
import os  # Importing os to interact with the file system
import simpleaudio as sa  # Importing simpleaudio to play .wav files
import threading  # Importing threading for concurrent execution of tasks
import time  # Importing time to manage timestamps and delays

# Function to create a connection to the MySQL database
def create_db_connection():
    conn = None  # Initialize the connection variable to None
    try:
        # Establish a connection to the MySQL database
        conn = mysql.connector.connect(
            host="localhost",  # The MySQL server address
            user="root",  # The MySQL username
            password="",  # The MySQL password
            database="users_db"  # The database to connect to
        )
    except mysql.connector.Error as e:  # Handle any connection errors
        print(f"Error connecting to MySQL: {e}")  # Print the error message
    return conn  # Return the connection object

# Function to validate user login credentials
def validate_user(username, password):
    conn = create_db_connection()  # Get a connection to the database
    if conn:  # If the connection is successful
        cursor = conn.cursor()  # Create a cursor object to interact with the database
        cursor.execute("SELECT password FROM users WHERE username = %s", (username,))  # Query to get the stored password for the username
        stored_password = cursor.fetchone()  # Fetch the stored password
        cursor.close()  # Close the cursor after executing the query
        conn.close()  # Close the database connection
        if stored_password and password == stored_password[0]:  # Check if the password matches
            return True  # Return True if the credentials are valid
    return False  # Return False if the credentials are invalid

# Function to add a new user to the database
def add_user(username, password):
    conn = create_db_connection()  # Get a connection to the database
    if conn:  # If the connection is successful
        cursor = conn.cursor()  # Create a cursor object to interact with the database
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))  # Query to check if the username already exists
        if cursor.fetchone():  # If a user with the same username is found
            messagebox.showerror("Sign Up", "Username already exists.")  # Show an error message
        else:
            cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, password))  # Insert the new user into the database
            conn.commit()  # Commit the changes to the database
            messagebox.showinfo("Sign Up", "Sign up successful!")  # Show a success message
        cursor.close()  # Close the cursor
        conn.close()  # Close the database connection

# Function to connect to the server
def connect_to_server(): 
    try:
        # Create a socket object and connect to the server at localhost on port 12345
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
        client_socket.connect(("127.0.0.1", 12345))  # Correct port
        return client_socket  # Return the socket connection if successful
    except Exception as e:  # If an error occurs while connecting to the server
        print(f"Error connecting to server: {e}")  # Print the error message
        return None  # Return None if the connection fails

# Class to manage the contacts window for sending voicemails
class ContactsWindow:
    def __init__(self, root, current_user):
        self.root = root  # Store the root window reference
        self.current_user = current_user  # Store the current user's username
        self.client_socket = connect_to_server()  # Establish a connection to the server
        if not self.client_socket:  # If the connection to the server fails
            messagebox.showerror("Connection Error", "Unable to connect to the server.")  # Show an error message
            return

        self.contacts = self.get_contacts()  # Fetch the list of contacts from the database
        self.received_voicemails = self.get_received_voicemails()  # Fetch the list of received voicemails
        self.latest_voicemail_path = None  # Initialize the variable to store the latest voicemail path
        self.setup_ui()  # Call the method to set up the user interface

    def get_contacts(self):
        conn = create_db_connection()  # Get a connection to the database
        contacts = []  # Initialize an empty list to store the contacts
        if conn:  # If the connection is successful
            cursor = conn.cursor()  # Create a cursor object
            cursor.execute("SELECT username FROM users WHERE username != %s", (self.current_user,))  # Query to get all users except the current user
            contacts = [username for (username,) in cursor.fetchall()]  # Fetch all usernames and store them in the contacts list
            cursor.close()  # Close the cursor
            conn.close()  # Close the database connection
        return contacts  # Return the list of contacts

    def get_received_voicemails(self):
        conn = create_db_connection()  # Get a connection to the database
        voicemails = []  # Initialize an empty list to store received voicemails
        if conn:  # If the connection is successful
            cursor = conn.cursor()  # Create a cursor object
            cursor.execute("SELECT voicemail_file_path, sender_username FROM voicemails WHERE receiver_username = %s", (self.current_user,))  # Query to get received voicemails
            voicemails = cursor.fetchall()  # Fetch all received voicemails
            cursor.close()  # Close the cursor
            conn.close()  # Close the database connection
        return voicemails  # Return the list of received voicemails

    def setup_ui(self):
        self.root.title("Contacts - Send Voicemail")  # Set the title of the window
        
        # Contact List Box
        self.contact_listbox = tk.Listbox(self.root, font=("Arial", 12), width=40, height=10)  # Create a Listbox widget for contacts
        self.contact_listbox.pack(pady=20)  # Pack the widget into the window with padding
        self.contact_listbox.insert(tk.END, *self.contacts)  # Insert the list of contacts into the Listbox

        # Received Voicemail List Box
        self.received_voicemail_listbox = tk.Listbox(self.root, font=("Arial", 12), width=40, height=10)  # Create a Listbox widget for received voicemails
        self.received_voicemail_listbox.pack(pady=20)  # Pack the widget into the window with padding
        for voicemail in self.received_voicemails:  # Loop through the received voicemails
            self.received_voicemail_listbox.insert(tk.END, f"From: {voicemail[1]} - {voicemail[0]}")  # Insert each voicemail into the Listbox

        # Buttons
        record_button = tk.Button(self.root, text="Record Voicemail", command=self.record_voicemail, font=("Arial", 12), padx=20, pady=10, bg="#4CAF50", fg="white")  # Create a button to record voicemail
        record_button.pack(pady=10)  # Pack the button into the window with padding

        listen_button = tk.Button(self.root, text="Listen to Voicemail", command=self.listen_received_voicemail, font=("Arial", 12), padx=20, pady=10, bg="#008CBA", fg="white")  # Create a button to listen to voicemail
        listen_button.pack(pady=10)  # Pack the button into the window with padding

    def listen_received_voicemail(self):
        selected_voicemail = self.received_voicemail_listbox.get(tk.ACTIVE)  # Get the selected voicemail from the list
        if selected_voicemail:  # If a voicemail is selected
            filename = selected_voicemail.split(' - ')[1]  # Extract the file path from the selected voicemail
            self.play_voicemail(filename)  # Play the selected voicemail
        else:
            messagebox.showerror("Listen Voicemail", "Please select a voicemail to listen.")  # Show an error if no voicemail is selected

    def play_voicemail(self, voicemail_filename):
        # Play the selected voicemail
        if os.path.exists(voicemail_filename):  # If the voicemail file exists
            try:
                wave_obj = sa.WaveObject.from_wave_file(voicemail_filename)  # Create a wave object from the voicemail file
                play_obj = wave_obj.play()  # Play the wave object
                play_obj.wait_done()  # Wait until the audio finishes playing
            except Exception as e:  # Handle any errors that occur while playing the voicemail
                messagebox.showerror("Listen Voicemail", f"Error playing voicemail: {e}")  # Show an error message
        else:
            messagebox.showerror("Listen Voicemail", "Voicemail file not found.")  # Show an error if the voicemail file is not found

    def send_voicemail(self):
        selected_contact = self.contact_listbox.get(tk.ACTIVE)  # Get the selected contact from the list
        if selected_contact and self.latest_voicemail_path:  # If a contact is selected and a voicemail is recorded
            voicemail_file = self.latest_voicemail_path  # Get the path to the latest voicemail
            if os.path.exists(voicemail_file):  # If the voicemail file exists
                conn = create_db_connection()  # Get a connection to the database
                if conn:  # If the connection is successful
                    cursor = conn.cursor()  # Create a cursor object
                    try:
                        # Insert the voicemail data into the database
                        cursor.execute("INSERT INTO voicemails (sender_username, receiver_username, voicemail_file_path) VALUES (%s, %s, %s)",
                                       (self.current_user, selected_contact, voicemail_file)) 
                        conn.commit()  # Commit the changes to the database
                        messagebox.showinfo("Send Voicemail", f"Voicemail sent to {selected_contact} successfully!")  # Show a success message
                    except mysql.connector.Error as e:  # Handle any database errors
                        messagebox.showerror("Send Voicemail", f"Error sending voicemail: {e}")  # Show an error message
                    finally:
                        cursor.close()  # Close the cursor
                        conn.close()  # Close the database connection

                self.client_socket.send(f"Voicemail to {selected_contact}".encode('utf-8'))  # Send a message to the server indicating the voicemail is sent
                response = self.client_socket.recv(1024).decode('utf-8')  # Wait for a response from the server
            else:
                messagebox.showerror("Send Voicemail", "No voicemail recorded yet.")  # Show an error if no voicemail is recorded
        else:
            messagebox.showerror("Send Voicemail", "Please select a contact or record a voicemail first.")  # Show an error if no contact is selected or voicemail is recorded

    def record_voicemail(self):
        self.record_window = tk.Toplevel(self.root)  # Create a new window for recording voicemail
        self.record_window.title("Recording Voicemail")  # Set the title of the recording window
        stop_button = tk.Button(self.record_window, text="Stop Recording", command=self.stop_recording, font=("Arial", 12), bg="#f44336", fg="white")  # Create a stop button
        stop_button.pack(pady=20)  # Pack the button into the window with padding
        self.is_recording = True  # Set the recording flag to True
        threading.Thread(target=self.record_and_enable_buttons).start()  # Start a new thread to record the voicemail

    def stop_recording(self):
        self.is_recording = False  # Set the recording flag to False to stop recording
        self.record_window.destroy()  # Destroy the recording window
        self.show_recorded_voicemail_screen()  # Show the screen for the recorded voicemail

    def record_and_enable_buttons(self):
        # Generate a unique filename for the voicemail
        voicemail_filename = f"voicemail_{int(time.time())}.wav"
        self.latest_voicemail_path = voicemail_filename  # Store the voicemail file path

        # Set up audio recording
        p = pyaudio.PyAudio()  # Initialize pyaudio
        stream = p.open(format=pyaudio.paInt16, channels=1, rate=44100, input=True, frames_per_buffer=1024)  # Open an audio stream
        frames = []  # Initialize an empty list to store audio frames

        # Record audio while is_recording is True
        while self.is_recording:
            frames.append(stream.read(1024))  # Append audio frames to the list

        # Stop and close the stream
        stream.stop_stream()  # Stop the audio stream
        stream.close()  # Close the audio stream
        p.terminate()  # Terminate pyaudio

        # Save the audio to a .wav file
        with wave.open(voicemail_filename, 'wb') as wf:  # Open the .wav file for writing
            wf.setnchannels(1)  # Set the number of channels (mono)
            wf.setsampwidth(p.get_sample_size(pyaudio.paInt16))  # Set the sample width
            wf.setframerate(44100)  # Set the frame rate (sampling rate)
            wf.writeframes(b''.join(frames))  # Write the audio frames to the file

        # Notify the user and enable the send button
        messagebox.showinfo("Record Voicemail", "Voicemail recorded successfully!")  # Show a success message
        self.send_button.config(state=tk.NORMAL)  # Enable the send button


    def show_recorded_voicemail_screen(self):
        self.recorded_voicemail_window = tk.Toplevel(self.root)  # Create a new window for the recorded voicemail
        listen_button = tk.Button(self.recorded_voicemail_window, text="Listen", command=self.listen_voicemail, font=("Arial", 12), bg="#4CAF50", fg="white")  # Create a listen button
        listen_button.pack(pady=10)  # Pack the button into the window with padding
        send_button = tk.Button(self.recorded_voicemail_window, text="Send", command=self.send_voicemail, font=("Arial", 12), bg="#f44336", fg="white")  # Create a send button
        send_button.pack(pady=10)  # Pack the button into the window with padding

    def listen_voicemail(self):
        if os.path.exists(self.latest_voicemail_path):  # If the voicemail file exists
            self.play_voicemail(self.latest_voicemail_path)  # Play the recorded voicemail
        else:
            messagebox.showerror("Listen Voicemail", "Recorded voicemail not found.")  # Show an error if the voicemail file is not found

# VoiceMail System App for login and main window
class VoiceMailSystemApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Voice Mail System")
        self.root.geometry("400x400")
        self.root.configure(bg="#f0f0f0")
        self.setup_ui()

    def setup_ui(self):
        # Title label
        title_label = tk.Label(self.root, text="Voice Mail System", bg="#f7f7f7", font=("Arial", 20, "bold"), fg="#333")
        title_label.pack(pady=20)

        # Username input field
        tk.Label(self.root, text="Username", bg="#f0f0f0", font=("Arial", 15)).pack(pady=3.5)
        self.username_entry = tk.Entry(self.root, font=("Arial", 12), bd=2., width=29)
        self.username_entry.pack(pady=5)

        # Password input field
        tk.Label(self.root, text="Password", bg="#f0f0f0", font=("Arial", 15)).pack(pady=3.5)
        self.password_entry = tk.Entry(self.root, show="*", font=("Arial", 12), bd=2., width=29)
        self.password_entry.pack(pady=5)

        # Login and Sign Up buttons
        tk.Button(self.root, text="Login", command=self.login, font=("Arial", 12), padx=22, pady=12, bg="#4CAF50", fg="white").pack(pady=10)
        tk.Button(self.root, text="Sign Up", command=self.sign_up, font=("Arial", 12), padx=20, pady=12, bg="#008CBA", fg="white").pack(pady=10)

    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        if validate_user(username, password):
            self.root.destroy()
            main_window = tk.Tk()
            contacts_window = ContactsWindow(main_window, username)
            main_window.mainloop()
        else:
            messagebox.showerror("Login Failed", "Invalid username or password.")

    def sign_up(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        add_user(username, password)

if __name__ == "__main__":
    root = tk.Tk()
    app = VoiceMailSystemApp(root)
    root.mainloop()
