from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                            QLabel, QTableWidget, QTableWidgetItem, QFileDialog,
                            QFrame, QHeaderView, QMessageBox, QDialog, QVBoxLayout,
                            QLineEdit, QComboBox)
from PyQt6.QtCore import Qt, pyqtSignal, QObject
from PyQt6.QtGui import QFont, QIcon, QPixmap
import os
import json
import datetime
import base64
import requests
import tempfile
import uuid
from db_manager import DatabaseManager
from firebase_admin import firestore
from firebase_config import db, FIREBASE_CONFIG
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
import fitz  # PyMuPDF
import cloudinary
import cloudinary.uploader
from cloudinary_config import get_cloudinary, config as cloudinary_config

# Create icons directory if it doesn't exist
icons_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'icons')
os.makedirs(icons_dir, exist_ok=True)

class PDFEncryption:
    @staticmethod
    def encrypt_pdf(pdf_path):
        """Encrypt a PDF file using AES encryption"""
        try:
            with open(pdf_path, "rb") as f:
                pdf_data = f.read()
            key = get_random_bytes(16)  # AES-128 bit key
            cipher = AES.new(key, AES.MODE_EAX)
            ciphertext, tag = cipher.encrypt_and_digest(pdf_data)
            return {
                'nonce': cipher.nonce,
                'ciphertext': ciphertext,
                'tag': tag,
                'key': key
            }
        except Exception as e:
            raise Exception(f"Encryption failed: {str(e)}")

    @staticmethod
    def decrypt_pdf(encrypted_data, key):
        """Decrypt a PDF file using AES encryption"""
        try:
            # Extract components
            nonce = encrypted_data[:16]
            tag = encrypted_data[16:32]
            ciphertext = encrypted_data[32:]
            
            # Create cipher and decrypt
            cipher = AES.new(key, AES.MODE_EAX, nonce)
            decrypted_data = cipher.decrypt_and_verify(ciphertext, tag)
            return decrypted_data
        except Exception as e:
            raise Exception(f"Decryption failed: {str(e)}")

class SecurePDFViewer(QDialog):
    def __init__(self, pdf_data, parent=None):
        super().__init__(parent)
        self.pdf_data = pdf_data
        self.current_page = 0
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle("Secure PDF Viewer")
        self.setMinimumSize(800, 600)
        layout = QVBoxLayout(self)
        
        # PDF display area
        self.page_label = QLabel()
        self.page_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.page_label)
        
        # Navigation buttons
        nav_layout = QHBoxLayout()
        self.prev_btn = QPushButton("Previous")
        self.next_btn = QPushButton("Next")
        self.prev_btn.clicked.connect(self.previous_page)
        self.next_btn.clicked.connect(self.next_page)
        nav_layout.addWidget(self.prev_btn)
        nav_layout.addWidget(self.next_btn)
        layout.addLayout(nav_layout)
        
        # Load first page
        self.doc = fitz.open(stream=self.pdf_data, filetype="pdf")
        self.total_pages = len(self.doc)
        self.load_current_page()
        
    def load_current_page(self):
        if 0 <= self.current_page < self.total_pages:
            page = self.doc.load_page(self.current_page)
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x zoom for better quality
            img_data = pix.tobytes("ppm")
            
            pixmap = QPixmap()
            pixmap.loadFromData(img_data)
            scaled_pixmap = pixmap.scaled(self.page_label.size(), 
                                        Qt.AspectRatioMode.KeepAspectRatio,
                                        Qt.TransformationMode.SmoothTransformation)
            self.page_label.setPixmap(scaled_pixmap)
            
            # Update button states
            self.prev_btn.setEnabled(self.current_page > 0)
            self.next_btn.setEnabled(self.current_page < self.total_pages - 1)
            
    def previous_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.load_current_page()
            
    def next_page(self):
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self.load_current_page()
            
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.load_current_page()  # Reload page with new size

class SecureShareDialog(QDialog):
    def __init__(self, file_name, file_path, user_id, parent=None):
        super().__init__(parent)
        self.file_name = file_name
        self.file_path = file_path
        self.user_id = user_id
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle("Secure Share PDF")
        layout = QVBoxLayout(self)
        
        # Preview button
        preview_btn = QPushButton("Preview PDF")
        preview_btn.clicked.connect(self.preview_pdf)
        layout.addWidget(preview_btn)
        
        # Recipient selection
        recipient_label = QLabel("Share with:")
        self.recipient_input = QLineEdit()
        self.recipient_input.setPlaceholderText("Enter recipient email or username")
        layout.addWidget(recipient_label)
        layout.addWidget(self.recipient_input)
        
        # Access level
        access_label = QLabel("Access Level:")
        self.access_combo = QComboBox()
        self.access_combo.addItems(["View Only", "View and Share"])
        layout.addWidget(access_label)
        layout.addWidget(self.access_combo)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        share_btn = QPushButton("Share")
        share_btn.clicked.connect(self.share_file)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        buttons_layout.addWidget(share_btn)
        buttons_layout.addWidget(cancel_btn)
        layout.addLayout(buttons_layout)
        
    def preview_pdf(self):
        """Preview the PDF in the secure viewer"""
        try:
            with open(self.file_path, 'rb') as f:
                pdf_data = f.read()
            viewer = SecurePDFViewer(pdf_data, self)
            viewer.exec()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not preview PDF: {str(e)}")
        
    def share_file(self):
        recipient = self.recipient_input.text().strip()
        access_level = self.access_combo.currentText()
        
        print("\n=== Starting PDF Share Process ===")
        print(f"Recipient: {recipient}")
        print(f"Access Level: {access_level}")
        print(f"File Path: {self.file_path}")
        print(f"File Name: {self.file_name}")
        
        if not recipient:
            print("Error: No recipient specified")
            QMessageBox.warning(self, "Error", "Please enter a recipient email")
            return
            
        # Show progress message
        progress_msg = QMessageBox(self)
        progress_msg.setIcon(QMessageBox.Icon.Information)
        progress_msg.setText("Processing file for secure sharing...")
        progress_msg.setStandardButtons(QMessageBox.StandardButton.NoButton)
        progress_msg.show()
        
        # Encrypt and upload file
        try:
            # Validate file exists and is readable
            print("\nValidating file...")
            if not os.path.exists(self.file_path):
                raise Exception(f"File not found at path: {self.file_path}")
                
            if not os.path.isfile(self.file_path):
                raise Exception(f"Invalid file path: {self.file_path}")
            
            print("File validation successful")
                
            # Encrypt the PDF
            print("\nEncrypting PDF...")
            try:
                encryption_result = PDFEncryption.encrypt_pdf(self.file_path)
                print("PDF encryption successful")
            except Exception as encrypt_err:
                print(f"Encryption error: {str(encrypt_err)}")
                raise Exception(f"Failed to encrypt PDF: {str(encrypt_err)}")
            
            # Combine encrypted components for storage
            encrypted_data = encryption_result['nonce'] + encryption_result['tag'] + encryption_result['ciphertext']
            
            # Configure Cloudinary
            print("\nConfiguring Cloudinary...")
            if not cloudinary_config:
                raise Exception("Cloudinary configuration not found or invalid")
                
            try:
                cloudinary.config(**cloudinary_config)
                print("Cloudinary configuration successful")
            except Exception as cloud_err:
                print(f"Cloudinary configuration error: {str(cloud_err)}")
                raise Exception(f"Failed to configure Cloudinary: {str(cloud_err)}")
            
            # Generate unique file identifier
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_id = base64.urlsafe_b64encode(os.urandom(8)).decode('ascii')
            secure_filename = f"{timestamp}_{unique_id}_{self.file_name}"
            print(f"\nGenerated secure filename: {secure_filename}")
            
            # Create temporary file for upload
            print("\nPreparing file for upload...")
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix='.bin') as tmp_file:
                    tmp_file.write(encrypted_data)
                    tmp_path = tmp_file.name
                print(f"Temporary file created at: {tmp_path}")
                
                # Upload to Cloudinary
                print("\nUploading to Cloudinary...")
                result = cloudinary.uploader.upload(
                    tmp_path,
                    resource_type="raw",
                    public_id=f"secure_pdfs/{secure_filename}",
                    folder="secure_pdfs",
                    use_filename=True,
                    unique_filename=True
                )
                print("Upload to Cloudinary successful")
                print(f"Cloudinary URL: {result.get('secure_url', 'Not available')}")
            except Exception as upload_err:
                print(f"Upload error: {str(upload_err)}")
                raise Exception(f"Failed to upload file: {str(upload_err)}")
            finally:
                # Clean up temporary file
                try:
                    os.unlink(tmp_path)
                    print("Temporary file cleaned up")
                except Exception as cleanup_err:
                    print(f"Warning: Failed to clean up temporary file: {str(cleanup_err)}")
            
            if not result or 'secure_url' not in result:
                raise Exception("Failed to get secure URL from Cloudinary")
            
            # Get geolocation
            print("\nGetting geolocation...")
            try:
                response = requests.get('https://ipapi.co/json/')
                location = response.json()
                geolocation = f"{location.get('city', 'Unknown')}, {location.get('country_name', 'Unknown')}"
                print(f"Geolocation: {geolocation}")
            except Exception as geo_err:
                print(f"Geolocation error: {str(geo_err)}")
                geolocation = "Unknown"
            
            # Create secure share record
            print("\nCreating share record...")
            share_data = {
                'file_name': self.file_name,
                'secure_filename': secure_filename,
                'original_path': self.file_path,
                'owner_id': self.user_id,
                'uploaded_at': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'encryption_key': encryption_result['key'].hex(),  # Store key as hex string
                'cloudinary_url': result['secure_url'],
                'access_records': [{
                    'user_id': self.user_id,
                    'action': 'upload',
                    'location': geolocation,
                    'time': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }],
                'share_chain': [{
                    'user_id': self.user_id,
                    'shared_with': recipient,
                    'access_level': access_level,
                    'time': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'location': geolocation
                }]
            }
            
            # Save to Firebase
            print("\nSaving to Firebase...")
            if not db:
                print("Error: Firebase database connection not available")
                print(f"Firebase config: {FIREBASE_CONFIG}")
                raise Exception("Database connection not available")
                
            try:
                doc_ref = db.collection('secure_files').add(share_data)
                print(f"Firebase document created with ID: {doc_ref[1].id}")
            except Exception as db_err:
                print(f"Firebase error: {str(db_err)}")
                raise Exception(f"Failed to save to database: {str(db_err)}")
            
            # Close progress message
            progress_msg.close()
            
            print("\n=== PDF Share Process Completed Successfully ===")
            QMessageBox.information(self, "Success", 
                                  f"File '{self.file_name}' has been securely shared with {recipient}")
            self.accept()
                
        except Exception as e:
            # Close progress message
            progress_msg.close()
            
            error_msg = str(e)
            print("\n=== PDF Share Process Failed ===")
            print(f"Error type: {type(e).__name__}")
            print(f"Error message: {error_msg}")
            print("Full error traceback:")
            import traceback
            traceback.print_exc()
            
            QMessageBox.critical(self, "Error", 
                               f"Failed to share file:\n\n{error_msg}\n\nPlease try again.")
            return False 

class FileTrackerWindow(QWidget):
    def __init__(self, user_id, parent=None):
        super().__init__(parent)
        self.user_id = user_id
        self.db_manager = DatabaseManager()
        self.setup_ui()
        self.load_file_access_records()
        
    def setup_ui(self):
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # Title
        title = QLabel("Track My Files")
        title.setObjectName("page-title")
        title.setFont(QFont(self.font().family(), 24, QFont.Weight.Bold))
        main_layout.addWidget(title)
        
        # Upload section
        upload_frame = QFrame()
        upload_frame.setObjectName("upload-section")
        upload_layout = QVBoxLayout(upload_frame)
        
        upload_label = QLabel("Upload a file to track who opens it and where")
        upload_label.setObjectName("section-label")
        
        upload_btn = QPushButton("Upload New File")
        upload_btn.setObjectName("primary-button")
        upload_btn.clicked.connect(self.upload_file)
        
        upload_layout.addWidget(upload_label)
        upload_layout.addWidget(upload_btn, alignment=Qt.AlignmentFlag.AlignLeft)
        main_layout.addWidget(upload_frame)
        
        # Files access records table
        table_label = QLabel("File Access Records")
        table_label.setObjectName("section-label")
        main_layout.addWidget(table_label)
        
        self.files_table = QTableWidget()
        self.files_table.setColumnCount(5)
        self.files_table.setHorizontalHeaderLabels(["File Name", "Accessed By", "Location", "Device", "Time"])
        self.files_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.files_table.setAlternatingRowColors(True)
        self.files_table.setObjectName("files-table")
        main_layout.addWidget(self.files_table)
        
        # Buttons row
        buttons_layout = QHBoxLayout()
        
        refresh_btn = QPushButton("Refresh")
        refresh_btn.setObjectName("secondary-button")
        refresh_btn.clicked.connect(self.load_file_access_records)
        
        delete_btn = QPushButton("Delete Selected")
        delete_btn.setObjectName("danger-button")
        delete_btn.clicked.connect(self.delete_selected_record)
        
        buttons_layout.addWidget(refresh_btn)
        buttons_layout.addWidget(delete_btn)
        buttons_layout.addStretch()
        
        main_layout.addLayout(buttons_layout)
        
        # Apply styles
        self.setStyleSheet("""
            QLabel#page-title {
                color: #2C3E50;
                margin-bottom: 15px;
            }
            QLabel#section-label {
                color: #34495E;
                font-size: 16px;
                font-weight: bold;
                margin-top: 10px;
                margin-bottom: 5px;
            }
            QFrame#upload-section {
                background-color: #ECF0F1;
                border-radius: 10px;
                padding: 15px;
                margin-bottom: 10px;
            }
            QPushButton#primary-button {
                background-color: #3498DB;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton#primary-button:hover {
                background-color: #2980B9;
            }
            QPushButton#secondary-button {
                background-color: #7F8C8D;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 5px;
            }
            QPushButton#secondary-button:hover {
                background-color: #95A5A6;
            }
            QPushButton#danger-button {
                background-color: #E74C3C;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 5px;
            }
            QPushButton#danger-button:hover {
                background-color: #C0392B;
            }
            QTableWidget#files-table {
                border: 1px solid #BDC3C7;
                border-radius: 5px;
            }
            QTableWidget#files-table::item {
                padding: 5px;
            }
            QHeaderView::section {
                background-color: #34495E;
                color: white;
                padding: 5px;
                border: none;
            }
        """)
        
    def upload_file(self):
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Select File to Track", "", "PDF Files (*.pdf)"
            )
            
            if file_path:
                # Validate file exists and is readable
                if not os.path.exists(file_path):
                    raise Exception("Selected file does not exist")
                    
                if not os.path.isfile(file_path):
                    raise Exception("Selected path is not a file")
                    
                # Try to open the file to verify it's readable
                try:
                    with open(file_path, 'rb') as f:
                        # Just read a small portion to verify it's accessible
                        f.read(1024)
                except Exception as e:
                    raise Exception(f"Cannot read selected file: {str(e)}")
                
                file_name = os.path.basename(file_path)
                
                # Show secure share dialog
                dialog = SecureShareDialog(file_name, file_path, self.user_id, self)
                dialog.exec()
                
                # Refresh the file list after upload
                self.load_file_access_records()
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to upload file: {str(e)}")
    
    def load_file_access_records(self):
        try:
            print("\n=== Loading File Access Records ===")
            self.files_table.setRowCount(0)  # Clear existing rows
            
            if not db:
                print("Error: Firebase database connection not available")
                raise Exception("Database connection not available")
            
            try:
                # Get tracked files using the recommended filter syntax
                print("Querying Firebase for tracked files...")
                tracked_files = (db.collection('secure_files')
                               .where(filter=firestore.FieldFilter("owner_id", "==", self.user_id))
                               .get())
                print(f"Found {len(list(tracked_files))} tracked files")
                
                # Flatten all access records into a single list
                all_access_records = []
                
                for file_doc in tracked_files:
                    file_data = file_doc.to_dict()
                    file_name = file_data.get('file_name', 'Unknown')
                    print(f"\nProcessing records for file: {file_name}")
                    
                    # Add share chain information
                    for share in file_data.get('share_chain', []):
                        all_access_records.append({
                            'file_name': file_name,
                            'user_name': f"Shared with: {share.get('shared_with', 'Unknown')}",
                            'location': share.get('location', 'Unknown'),
                            'device': share.get('access_level', 'Unknown'),
                            'time': share.get('time', 'Unknown'),
                            'record_id': file_doc.id,
                            'action': 'share'
                        })
                    
                    # Add access records
                    for record in file_data.get('access_records', []):
                        all_access_records.append({
                            'file_name': file_name,
                            'user_name': record.get('user_name', 'Unknown'),
                            'location': record.get('location', 'Unknown'),
                            'device': record.get('device', 'Unknown'),
                            'time': record.get('time', 'Unknown'),
                            'record_id': file_doc.id,
                            'action': record.get('action', 'view')
                        })
                
                print(f"\nTotal records to display: {len(all_access_records)}")
                
                # Sort records by time (newest first)
                all_access_records.sort(key=lambda x: x.get('time', ''), reverse=True)
                
                # Populate table
                self.files_table.setRowCount(len(all_access_records))
                
                for row, record in enumerate(all_access_records):
                    self.files_table.setItem(row, 0, QTableWidgetItem(record['file_name']))
                    self.files_table.setItem(row, 1, QTableWidgetItem(record['user_name']))
                    self.files_table.setItem(row, 2, QTableWidgetItem(record['location']))
                    self.files_table.setItem(row, 3, QTableWidgetItem(record['device']))
                    self.files_table.setItem(row, 4, QTableWidgetItem(record['time']))
                    
                    # Style different actions differently
                    if record['action'] == 'upload':
                        color = Qt.GlobalColor.lightGray
                    elif record['action'] == 'share':
                        color = Qt.GlobalColor.cyan
                    else:
                        color = Qt.GlobalColor.white
                    
                    for col in range(5):
                        item = self.files_table.item(row, col)
                        item.setBackground(color)
                        font = item.font()
                        font.setBold(True)
                        item.setFont(font)
                
                print("=== File Access Records Loaded Successfully ===")
                    
            except Exception as db_err:
                print(f"Firebase error: {str(db_err)}")
                raise Exception(f"Failed to load records from database: {str(db_err)}")
                
        except Exception as e:
            error_msg = str(e)
            print("\n=== Failed to Load File Access Records ===")
            print(f"Error type: {type(e).__name__}")
            print(f"Error message: {error_msg}")
            print("Full error traceback:")
            import traceback
            traceback.print_exc()
            
            QMessageBox.critical(self, "Error", f"Failed to load file records: {error_msg}")
    
    def delete_selected_record(self):
        try:
            current_row = self.files_table.currentRow()
            
            if current_row >= 0:
                file_name = self.files_table.item(current_row, 0).text()
                
                reply = QMessageBox.question(
                    self, "Confirm Delete", 
                    f"Are you sure you want to delete the record for '{file_name}'?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                
                if reply == QMessageBox.StandardButton.Yes:
                    # In a real app, you would delete the specific access record
                    # For now, we'll just refresh the table
                    self.files_table.removeRow(current_row)
                    QMessageBox.information(self, "Success", "Record deleted successfully")
            else:
                QMessageBox.warning(self, "Warning", "Please select a record to delete")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to delete record: {str(e)}")
    
    def cleanup(self):
        # Any cleanup operations can go here
        pass 