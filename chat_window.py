def download_and_open_file_safely(self, url, filename):
        """Downloads a file and opens it with appropriate application, with robust error handling"""
        print(f"\n==== DOWNLOADING AND OPENING FILE SAFELY ====")
        print(f"URL: {url}")
        print(f"Filename: {filename}")
        
        try:
            # Show download status message
            self.web_page.runJavaScript(f'''
                try {{
                    var status = document.createElement('div');
                    status.id = 'download-status';
                    status.style.position = 'fixed';
                    status.style.bottom = '20px';
                    status.style.left = '50%';
                    status.style.transform = 'translateX(-50%)';
                    status.style.backgroundColor = '#4682B4';
                    status.style.color = 'white';
                    status.style.padding = '10px 20px';
                    status.style.borderRadius = '5px';
                    status.style.zIndex = '9999';
                    status.innerHTML = 'Downloading {filename}...';
                    document.body.appendChild(status);
                }} catch(e) {{
                    console.error("Error showing download status: " + e);
                }}
            ''')
            
            # Create a temporary directory for downloads if it doesn't exist
            temp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'temp')
            os.makedirs(temp_dir, exist_ok=True)
            
            # Get file extension
            _, ext = os.path.splitext(filename)
            if not ext:
                # Default to PDF for files without extension
                ext = '.pdf'
            
            # Create a temporary file with the correct extension
            temp_file_path = os.path.join(temp_dir, f"mindly_tmp_{int(datetime.datetime.now().timestamp())}{ext}")
            print(f"Temporary file path: {temp_file_path}")
            
            # Download the file
            print("Starting download...")
            
            # Use urllib to download the file
            import urllib.request
            urllib.request.urlretrieve(url, temp_file_path)
            print(f"File downloaded successfully to {temp_file_path}")
            
            # Update status message
            self.web_page.runJavaScript('''
                try {
                    var status = document.getElementById('download-status');
                    if (status) {
                        status.innerHTML = 'Opening file...';
                        setTimeout(function() {
                            status.parentNode.removeChild(status);
                        }, 2000);
                    }
                } catch(e) {
                    console.error("Error updating status: " + e);
                }
            ''')
            
            # Open the file with the default application based on OS
            print(f"Opening file with default application...")
            
            # Use platform-specific methods to open the file
            if os.name == 'nt':  # Windows
                os.startfile(os.path.normpath(temp_file_path))
                print("File opened with Windows default application")
            elif sys.platform == 'darwin':  # macOS
                subprocess.run(['open', temp_file_path], check=True)
                print("File opened with macOS default application")
            else:  # Linux
                subprocess.run(['xdg-open', temp_file_path], check=True)
                print("File opened with Linux default application")
            
            print("File opened successfully")
            
        except Exception as e:
            print(f"ERROR: {str(e)}")
            print(f"Error type: {type(e).__name__}")
            import traceback
            print("Full traceback:")
            traceback.print_exc()
            
            # Show error message to user
            self.web_page.runJavaScript(f'''
                try {{
                    var status = document.getElementById('download-status');
                    if (status) {{
                        status.style.backgroundColor = '#D9534F';
                        status.innerHTML = 'Error: {str(e).replace("'", "\\'")}';
                        setTimeout(function() {{
                            status.parentNode.removeChild(status);
                        }}, 5000);
                    }}
                }} catch(e) {{
                    console.error("Error showing error message: " + e);
                    alert("Error opening file: {str(e).replace("'", "\\'")}");
                }}
            ''')
            
            QMessageBox.warning(self, "Error Opening File", 
                               f"Failed to open file: {filename}\n\nError: {str(e)}\n\n"
                               f"Please check your internet connection and try again.") 