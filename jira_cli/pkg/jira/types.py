"""JIRA data types as Pydantic models.

Converted from pkg/jira/types.go
"""

from enum import Enum
from typing import Dict, List, Any, Optional

from pydantic import AliasChoices, BaseModel, Field as PydanticField


class AuthType(str, Enum):
    """Jira authentication type."""

    BASIC = "basic"
    BEARER = "bearer"
    MTLS = "mtls"

    def __str__(self) -> str:
        return self.value


# API version constants
INSTALLATION_TYPE_CLOUD = "Cloud"
INSTALLATION_TYPE_LOCAL = "Local"

BASE_URL_V3 = "/rest/api/3"
BASE_URL_V2 = "/rest/api/2"
BASE_URL_V1 = "/rest/agile/1.0"

# Issue type constants
ISSUE_TYPE_EPIC = "Epic"
ISSUE_TYPE_SUB_TASK = "Sub-task"

# Assignee constants
ASSIGNEE_NONE = "none"
ASSIGNEE_DEFAULT = "default"

# Field name constants
EPIC_FIELD_NAME = "Epic Name"
EPIC_FIELD_LINK = "Epic Link"


class MTLSConfig(BaseModel):
    """mTLS authentication config."""

    ca_cert: str = ""
    client_cert: str = ""
    client_key: str = ""


class Project(BaseModel):
    """Project info."""

    model_config = {"extra": "ignore", "populate_by_name": True}

    id: str = ""
    key: str
    name: str
    lead: Dict[str, Any] = PydanticField(default_factory=lambda: {"displayName": ""})
    type: str = PydanticField(
        default="",
        validation_alias=AliasChoices("style", "projectTypeKey"),
    )


class ProjectVersion(BaseModel):
    """Project version info."""

    archived: bool = False
    description: Optional[str] = None
    id: str
    name: str
    project_id: int = PydanticField(default=0, alias="projectId")
    released: bool = False


class Board(BaseModel):
    """Board info."""

    id: int
    name: str
    type: str = PydanticField(default="", alias="type")


class Epic(BaseModel):
    """Epic info."""

    name: str = ""
    link: str = ""


class User(BaseModel):
    """User info."""

    account_id: Optional[str] = PydanticField(default=None, alias="accountId")
    email: str = PydanticField(default="", alias="emailAddress")
    name: str = ""
    display_name: str = PydanticField(default="", alias="displayName")
    active: bool = True

    @property
    def login(self) -> str:
        """Get login identifier (email for cloud, name for local)."""
        return self.email or self.name


class IssueType(BaseModel):
    """Issue type info."""

    model_config = {"extra": "ignore"}

    id: str
    name: str
    handle: str = PydanticField(default="", alias="untranslatedName")
    subtask: bool = PydanticField(default=False, alias="subtask")


class IssueFields(BaseModel):
    """Issue fields."""

    model_config = {"populate_by_name": True, "extra": "ignore"}

    summary: str = ""
    description: Any = None  # str in v1/v2, ADF dict in v3
    labels: List[str] = PydanticField(default_factory=list)
    resolution: Optional[Dict[str, Any]] = PydanticField(default_factory=lambda: {"name": ""})
    issue_type: IssueType = PydanticField(
        default_factory=lambda: IssueType(id="", name=""),
        validation_alias=AliasChoices("issueType", "issuetype"),
    )
    parent: Optional[Dict[str, Any]] = None
    assignee: Optional[Dict[str, Any]] = PydanticField(default_factory=lambda: {"displayName": ""})
    priority: Optional[Dict[str, Any]] = PydanticField(default_factory=lambda: {"name": ""})
    reporter: Optional[Dict[str, Any]] = PydanticField(default_factory=lambda: {"displayName": ""})
    watches: Dict[str, Any] = PydanticField(
        default_factory=lambda: {"isWatching": False, "watchCount": 0}
    )
    status: Dict[str, Any] = PydanticField(default_factory=lambda: {"name": ""})
    components: List[Dict[str, Any]] = PydanticField(default_factory=list)
    fix_versions: List[Dict[str, Any]] = PydanticField(
        default_factory=list,
        validation_alias=AliasChoices("fixVersions", "fixversions"),
    )
    affects_versions: List[Dict[str, Any]] = PydanticField(default_factory=list, alias="versions")
    comment: Dict[str, Any] = PydanticField(
        default_factory=lambda: {"comments": [], "total": 0}
    )
    subtasks: List["Issue"] = PydanticField(default_factory=list)
    issue_links: List[Dict[str, Any]] = PydanticField(
        default_factory=list,
        validation_alias=AliasChoices("issueLinks", "issuelinks"),
    )
    created: str = ""
    updated: str = ""


class Issue(BaseModel):
    """Issue info."""

    model_config = {"extra": "ignore"}

    key: str
    fields: IssueFields = PydanticField(default_factory=IssueFields)


class Field(BaseModel):
    """Field info."""

    id: str
    name: str
    custom: bool = False
    field_schema: Dict[str, Any] = PydanticField(default_factory=dict, alias="schema")


class IssueTypeField(BaseModel):
    """Issue type field info."""

    name: str
    key: str
    field_schema: Dict[str, str] = PydanticField(default_factory=dict, alias="schema")
    field_id: str = PydanticField(default="", alias="fieldId")


class IssueLinkType(BaseModel):
    """Issue link type info."""

    id: str
    name: str
    inward: str
    outward: str


class Sprint(BaseModel):
    """Sprint info."""

    id: int
    name: str
    status: str = PydanticField(default="", alias="state")
    start_date: str = PydanticField(default="", alias="startDate")
    end_date: str = PydanticField(default="", alias="endDate")
    complete_date: str = PydanticField(default="", alias="completeDate")
    board_id: int = PydanticField(default=0, alias="originBoardId")


class Transition(BaseModel):
    """Issue transition info."""

    id: str
    name: str
    is_available: bool = PydanticField(default=True, alias="isAvailable")


class SearchResult(BaseModel):
    """Search result."""

    issues: List[Issue] = PydanticField(default_factory=list)
    total: int = 0
    start_at: int = PydanticField(default=0, alias="startAt")
    max_results: int = PydanticField(default=100, alias="maxResults")


class CreateRequest(BaseModel):
    """Issue creation request."""

    model_config = {"populate_by_name": True}

    project: Dict[str, str]
    summary: str
    description: Any = None
    issue_type: Dict[str, str] = PydanticField(alias="issueType")
    parent: Optional[Dict[str, str]] = None
    assignee: Optional[Dict[str, str]] = None
    priority: Optional[Dict[str, str]] = None
    labels: List[str] = PydanticField(default_factory=list)
    components: List[Dict[str, str]] = PydanticField(default_factory=list)


class CreateResponse(BaseModel):
    """Issue creation response."""

    id: str
    key: str
    self: str = ""


class TransitionRequest(BaseModel):
    """Transition request."""

    transition: Dict[str, str]


class UserSearchOptions(BaseModel):
    """User search options."""

    query: str = ""
    project: str = ""
    issue_key: str = PydanticField(default="", alias="issueKey")
    max_results: int = PydanticField(default=50, alias="maxResults")


class Comment(BaseModel):
    """Issue comment."""

    model_config = {"populate_by_name": True, "extra": "ignore"}

    id: str
    body: Any = ""  # str in v2, ADF dict in v3
    author: Dict[str, Any] = PydanticField(default_factory=lambda: {"displayName": ""})
    update_author: Dict[str, Any] = PydanticField(default_factory=lambda: {"displayName": ""}, alias="updateAuthor")
    created: str = ""
    updated: str = ""


class CommentList(BaseModel):
    """List of comments."""

    comments: List[Comment] = PydanticField(default_factory=list)
    total: int = 0
    start_at: int = PydanticField(default=0, alias="startAt")
    max_results: int = PydanticField(default=50, alias="maxResults")


class Worklog(BaseModel):
    """Issue worklog entry."""

    model_config = {"populate_by_name": True, "extra": "ignore"}

    id: str
    comment: str = ""
    time_spent: str = PydanticField(default="", alias="timeSpent")
    time_spent_seconds: int = PydanticField(default=0, alias="timeSpentSeconds")
    author: Dict[str, Any] = PydanticField(default_factory=lambda: {"displayName": ""})
    started: str = ""
    created: str = ""


class WorklogList(BaseModel):
    """List of worklogs."""

    worklogs: List[Worklog] = PydanticField(default_factory=list)
    total: int = 0
    start_at: int = PydanticField(default=0, alias="startAt")
    max_results: int = PydanticField(default=50, alias="maxResults")