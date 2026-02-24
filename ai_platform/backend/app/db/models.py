from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Float, Table, JSON, Index
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

# Association table for Problem Tags (Many-to-Many)
problem_tag_association = Table(
    'problem_tag_association',
    Base.metadata,
    Column('problem_id', Integer, ForeignKey('problems.id', ondelete="CASCADE"), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tags.id', ondelete="CASCADE"), primary_key=True)
)

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    
    # Relationships
    skill_profile = relationship("UserSkillProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    submissions = relationship("Submission", back_populates="user", cascade="all, delete-orphan")

class UserSkillProfile(Base):
    """Tracks the dynamic skill metrics for the Adaptive Difficulty Engine."""
    __tablename__ = "user_skill_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    elo_rating = Column(Float, default=1200.0)
    total_solved = Column(Integer, default=0)
    total_attempts = Column(Integer, default=0)
    weak_tags = Column(JSON, default=dict)  # Stores dict of {tag_name: failure_rate}
    
    user = relationship("User", back_populates="skill_profile")

class Tag(Base):
    __tablename__ = "tags"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, index=True)
    
    problems = relationship("Problem", secondary=problem_tag_association, back_populates="tags")

class Problem(Base):
    __tablename__ = "problems"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    slug = Column(String(255), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=False)
    constraints = Column(Text, nullable=False)
    difficulty_level = Column(Integer, default=1)  # 1 to 10
    time_limit_ms = Column(Integer, default=2000)
    memory_limit_mb = Column(Integer, default=128)
    
    # Hidden test cases stored privately or linked to an S3 bucket in prod. Storing simple JSON for now.
    public_test_cases = Column(JSON, nullable=False)   # [{"input": "...", "expected": "...", "type": "normal"}]
    hidden_test_cases = Column(JSON, nullable=False)   # [{"input": "...", "expected": "...", "weight": 1.0}]
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    tags = relationship("Tag", secondary=problem_tag_association, back_populates="problems")
    submissions = relationship("Submission", back_populates="problem")

class Submission(Base):
    """Tracks a single code execution event against a Problem."""
    __tablename__ = "submissions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    problem_id = Column(Integer, ForeignKey("problems.id", ondelete="CASCADE"), index=True)
    
    code = Column(Text, nullable=False)
    language = Column(String(20), default="python")
    
    score = Column(Float, default=0.0)          # 0.0 to 100.0
    status = Column(String(50), index=True)     # "Pending", "Accepted", "Wrong Answer", "TLE", "MLE", "Error"
    time_taken_ms = Column(Integer, nullable=True)
    memory_used_mb = Column(Float, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="submissions")
    problem = relationship("Problem", back_populates="submissions")
    ai_analysis = relationship("AIAnalysis", back_populates="submission", uselist=False, cascade="all, delete-orphan")
    attempts = relationship("Attempt", back_populates="submission", cascade="all, delete-orphan")

class Attempt(Base):
    """Tracks granular execution metrics per test case for a Submission."""
    __tablename__ = "attempts"
    
    id = Column(Integer, primary_key=True, index=True)
    submission_id = Column(Integer, ForeignKey("submissions.id", ondelete="CASCADE"), index=True)
    test_case_id = Column(String(50))           # e.g., "public_1" or "hidden_2"
    passed = Column(Boolean, default=False)
    execution_time_ms = Column(Integer, nullable=True)
    stdout = Column(Text, nullable=True)
    stderr = Column(Text, nullable=True)
    
    submission = relationship("Submission", back_populates="attempts")

class AIAnalysis(Base):
    """Stores the LLM generated strict JSON output for caching and review."""
    __tablename__ = "ai_analyses"
    
    id = Column(Integer, primary_key=True, index=True)
    submission_id = Column(Integer, ForeignKey("submissions.id", ondelete="CASCADE"), unique=True)
    
    # Strictly validated JSON stored here
    error_analysis = Column(JSON, nullable=False)
    complexity_analysis = Column(JSON, nullable=False)
    hints = Column(JSON, nullable=False)
    test_cases_generated = Column(JSON, nullable=False)
    
    tokens_used = Column(Integer, default=0)    # Cost tracking
    latency_ms = Column(Integer, default=0)     # Observability
    created_at = Column(DateTime, default=datetime.utcnow)
    
    submission = relationship("Submission", back_populates="ai_analysis")

# Additional Indexes for performance querying on high-traffic columns
Index('ix_submissions_user_status', Submission.user_id, Submission.status)
Index('ix_skill_elo', UserSkillProfile.elo_rating)
