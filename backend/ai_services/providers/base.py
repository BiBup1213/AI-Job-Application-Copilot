from typing import Protocol


class AIProvider(Protocol):
    def evaluate_job_match(self, job):
        ...

    def generate_application_documents(self, application):
        ...

    def generate_follow_up_document(self, application):
        ...

    def classify_email_message(self, email):
        ...

    def suggest_profile_from_documents(self, profile, documents):
        ...
