from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone

from datetime import datetime, date, timedelta
from pathlib import Path
import logging
import json
import enum

class NewFile(models.Model):
    BASE_DIR = Path("I:/temp/Daily_temp/")
    
    class Meta:
        verbose_name = 'New File'
        verbose_name_plural = 'New Files'

    file_name = models.CharField(max_length=255)
    file_type = models.CharField(max_length=5)
    file_path = models.CharField(max_length=255)
    file_hash = models.CharField(max_length=255)
    file_created = models.DateTimeField()
    file_modified = models.DateTimeField()

    def __str__(self):
        return self.file_name
    
    def file_exists(self):
        return Path(self.file_path).exists()
    
    @classmethod
    def get_new_files(cls):
        """Detect new files in the base directory."""
        new_files = []
        for file in cls.objects.all():
            if not file.file_exists():
                file.delete()
            else:
                new_files.append(file)
        
        known_files = set([doc.file_path for doc in Document.objects.all()])
        known_files.update([file.file_path for file in new_files])
        for file in cls.BASE_DIR.glob('**/*'):
            if file.is_file() and str(file) not in known_files:
                new_file = cls(
                    file_name=file.name,
                    file_type=file.suffix,
                    file_path=str(file),
                    file_hash='0',
                    file_created=datetime.fromtimestamp(file.stat().st_ctime),
                    file_modified=datetime.fromtimestamp(file.stat().st_mtime),
                )
                new_file.save()
                new_files.append(new_file)
        return new_files

class Document(models.Model):
    class DocumentType(enum.Enum):
        PDF = 'PDF'
        DOCX = 'DOCX'
        XLSX = 'XLSX'
        CSV = 'CSV'
        TXT = 'TXT'
        UNKNOWN = 'UNKNOWN'

    class Meta:
        verbose_name = 'Document'
        verbose_name_plural = 'Documents'
    
    form_class = 'DocumentForm'

    file_name = models.CharField(max_length=255)
    file_hash = models.CharField(max_length=255)
    file_path = models.CharField(max_length=255, unique=True)
    file_type = models.CharField(max_length=5, choices=[(tag.value, tag.name) for tag in DocumentType])
    
    file_created = models.DateTimeField()
    file_modified = models.DateTimeField()
    
    file_category = models.ForeignKey('Category', on_delete=models.SET_NULL, null=True)

    doc_label = models.CharField(max_length=255, blank=True)
    doc_created = models.DateTimeField(auto_now_add=True)
    doc_modified = models.DateTimeField(auto_now=True)
    doc_tags = models.ManyToManyField('Tag', blank=True, related_name='tags')
    doc_notes = models.TextField(blank=True)

class DocumentExtension(models.Model):
    class Meta:
        abstract = True

    document = models.ForeignKey('Document', on_delete=models.CASCADE)

class Bill(DocumentExtension):
    class Meta:
        verbose_name = 'Bill'
        verbose_name_plural = 'Bills'
    bill_date = models.DateField()
    bill_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    form_class = 'BillForm'

class Category(models.Model):
    """Category model for grouping documents."""
    class Meta:
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'

    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    
    # A category has a document type (meaning either 'Document' or a subclass of 'DocumentExtension') associated with it
    # This does not point to a specific document, but rather to the model class
    doc_type = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    
    def get_doc_type(self):
        if self.doc_type == 'Document':
            return Document
        else:
            for subclass in DocumentExtension.__subclasses__():
                if subclass.__name__ == self.doc_type:
                    return subclass
        return None

    def __str__(self):
        return self.name

class Tag(models.Model):
    """Tag model for categorizing documents."""
    class Meta:
        verbose_name = 'Tag'
        verbose_name_plural = 'Tags'

    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)