from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class QuipMigrationFile(db.Model):
    __tablename__ = 'quip_migration_files'
    
    quip_migration_file_id = db.Column(db.BigInteger, primary_key=True)
    quip_id = db.Column(db.Text, nullable=False)
    quip_secret_path = db.Column(db.Text)
    google_drive_id = db.Column(db.Text)
    obfuscated_name = db.Column(db.Text)
    when_migration_completed = db.Column(db.DateTime)
    when_links_fixed = db.Column(db.DateTime)
    when_quip_last_edited = db.Column(db.DateTime)
    when_quip_created = db.Column(db.DateTime)
    parent_folders = db.Column(db.ARRAY(db.Text), nullable=False)
    document_type = db.Column(db.Text)
    html_content = db.Column(db.Text)
    author = db.Column(db.Text)
    owners = db.Column(db.ARRAY(db.Text), nullable=False)
    editors = db.Column(db.ARRAY(db.Text), nullable=False)
    commenters = db.Column(db.ARRAY(db.Text), nullable=False)
    viewers = db.Column(db.ARRAY(db.Text), nullable=False)
    when_updated = db.Column(db.DateTime)
    
    def __repr__(self):
        return f'<QuipMigrationFile {self.quip_id}: {self.obfuscated_name}>'

class QuipMigrationFolder(db.Model):
    __tablename__ = 'quip_migration_folders'
    
    quip_migration_folder_id = db.Column(db.BigInteger, primary_key=True)
    quip_id = db.Column(db.Text, nullable=False)
    google_drive_id = db.Column(db.Text)
    obfuscated_name = db.Column(db.Text, nullable=False)
    when_migration_completed = db.Column(db.DateTime)
    parent_folder = db.Column(db.Text)
    member_ids = db.Column(db.ARRAY(db.Text), nullable=False)
    inherit_mode = db.Column(db.Text, nullable=False)
    when_updated = db.Column(db.DateTime)
    
    def __repr__(self):
        return f'<QuipMigrationFolder {self.quip_id}: {self.obfuscated_name}>'

class GoogleDriveFile(db.Model):
    __tablename__ = 'google_drive_files'
    
    id = db.Column(db.Integer, primary_key=True)
    quip_document_id = db.Column(db.String(255), nullable=False)
    google_drive_file_id = db.Column(db.String(255), unique=True)
    google_drive_file_name = db.Column(db.String(500))
    google_drive_file_url = db.Column(db.String(1000))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<GoogleDriveFile {self.google_drive_file_id}: {self.google_drive_file_name}>'

class MigrationLog(db.Model):
    __tablename__ = 'migration_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.String(255), nullable=False)
    action = db.Column(db.String(100), nullable=False)  # import, export, migrate
    status = db.Column(db.String(50), nullable=False)  # success, failed, pending
    message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<MigrationLog {self.action}: {self.status}>'

# Keep the old models for backward compatibility
class QuipDocument(db.Model):
    __tablename__ = 'quip_documents'
    
    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.String(255), unique=True, nullable=False)
    title = db.Column(db.String(500))
    content = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    status = db.Column(db.String(50), default='pending')  # pending, migrated, failed
    
    def __repr__(self):
        return f'<QuipDocument {self.document_id}: {self.title}>' 