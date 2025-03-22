from dataclasses import dataclass
from typing import List, Optional, TypedDict

@dataclass
class Contact(TypedDict):
    id: int
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None

@dataclass
class Practice(TypedDict):
    id: int
    name: str
    category: str
    content: str
    author: str
    description: Optional[str] = None

@dataclass
class Link(TypedDict):
    title: Optional[str]
    url: Optional[str]

@dataclass
class University(TypedDict):
    id: int
    name: str
    instagram: str
    description: str
    link: Link

@dataclass
class Psychologist(TypedDict):
    id: int
    name: str
    price: int
    contacts: Contact
    instagram: str
    specialty: str

@dataclass
class Event(TypedDict):
    id: int
    universityId: int
    title: str
    date: str
    description: str
    link: str

@dataclass
class Partner(TypedDict):
    id: int
    name: str
    description: str
    link: Optional[str] = None
    
@dataclass
class BotInfo(TypedDict):
    start_text: str
    contacts: List[Contact]
    practices: List[Practice]
    universities: List[University]
    psychologists: List[Psychologist]
    events: List[Event]
    partners: List[Partner]

@dataclass
class Data(TypedDict):
    users: List[int]
    bot_info: BotInfo
    admin_ids: List[int]
