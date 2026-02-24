import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models import UserSkillProfile, Problem

# Map problem difficulty (1-10) to an Elo rating equivalent
DIFFICULTY_ELO_MAP = {
    1: 800,
    2: 1000,
    3: 1200,
    4: 1400,
    5: 1600,
    6: 1800,
    7: 2000,
    8: 2200,
    9: 2400,
    10: 2600
}

K_FACTOR = 32

class AdaptiveEloEngine:
    """
    Updates the user's skill profile based on submission performance.
    """

    @staticmethod
    def calculate_new_elo(current_user_elo: float, problem_elo: float, score: float) -> float:
        """
        Standard Elo formula.
        score is from 0.0 to 100.0, we normalize to 0.0 to 1.0 (0=loss, 1=win, partial=draw)
        """
        normalized_score = score / 100.0
        
        expected_score = 1 / (1 + 10 ** ((problem_elo - current_user_elo) / 400))
        new_elo = current_user_elo + K_FACTOR * (normalized_score - expected_score)
        
        return max(0.0, new_elo) # Prevent negative Elo

    @staticmethod
    async def update_user_skill(db: AsyncSession, user_id: int, problem_id: int, score: float, tags: list[str] = None):
        """
        Updates the UserSkillProfile in the database after a submission.
        """
        # Fetch user skill profile
        stmt = select(UserSkillProfile).where(UserSkillProfile.user_id == user_id)
        result = await db.execute(stmt)
        skill_profile = result.scalar_one_or_none()
        
        if not skill_profile:
            skill_profile = UserSkillProfile(user_id=user_id)
            db.add(skill_profile)
            
        # Fetch problem to get difficulty
        problem_stmt = select(Problem).where(Problem.id == problem_id)
        problem_result = await db.execute(problem_stmt)
        problem = problem_result.scalar_one_or_none()
        
        difficulty = problem.difficulty_level if problem else 1
        problem_elo = DIFFICULTY_ELO_MAP.get(difficulty, 1200)
        
        # Calculate new Elo
        new_elo = AdaptiveEloEngine.calculate_new_elo(skill_profile.elo_rating, problem_elo, score)
        
        # Update stats
        skill_profile.elo_rating = new_elo
        skill_profile.total_attempts += 1
        if score == 100.0:
            skill_profile.total_solved += 1
            
        # Update weak tags
        # If score is low, penalize the tags involved
        if score < 100.0 and tags:
            # We store tag_name: failure_count
            current_weak_tags = skill_profile.weak_tags.copy() if skill_profile.weak_tags else {}
            for tag in tags:
                current_weak_tags[tag] = current_weak_tags.get(tag, 0) + 1
            skill_profile.weak_tags = current_weak_tags
            
        await db.commit()
        return skill_profile
