from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class CertificateResponse(BaseModel):
    id: UUID
    student_id: UUID
    course_id: UUID
    certificate_number: str
    issued_at: datetime

    model_config = ConfigDict(from_attributes=True)