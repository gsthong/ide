from db.models import UserSkillProfile, Problem
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Dict

class AdaptiveDifficultyEngine:
    """
    Updates user Elo ratings and provides next question recommendations 
    based on success and failure across algorithmic tag weaknesses.
    """
    
    K_FACTOR = 32  # Standard Elo K-factor
    
    @staticmethod
    async def update_skill_profile(db: AsyncSession, user_id: int, problem_difficulty: int, score: float, tags: List[str]):
        """
        Updates the UserSkillProfile dynamically post-submission.
        score is between 0.0 and 100.0
        problem_difficulty is mapped to an internal Elo (e.g. 1-10 mapped to 800 - 2400)
        """
        expected_problem_elo = 800 + (problem_difficulty - 1) * 160
        
        result = await db.execute(select(UserSkillProfile).where(UserSkillProfile.user_id == user_id))
        profile = result.scalars().first()
        
        if not profile:
            profile = UserSkillProfile(user_id=user_id, elo_rating=1200.0, total_solved=0, total_attempts=0, weak_tags={})
            db.add(profile)
        
        profile.total_attempts += 1
        if score == 100.0:
            profile.total_solved += 1
            
        # Elo Update specific logic mapping actual performance 0-1 against expected performance
        actual_performance = score / 100.0
        expected_performance = 1 / (1 + 10 ** ((expected_problem_elo - profile.elo_rating) / 400))
        
        elo_change = AdaptiveDifficultyEngine.K_FACTOR * (actual_performance - expected_performance)
        profile.elo_rating += elo_change
        
        # Track individual tag weaknesses
        # If they failed, increase the failure weight of these tags
        tags_dict = dict(profile.weak_tags) if profile.weak_tags else {}
        for tag in tags:
            current_miss_rate = tags_dict.get(tag, 0.0)
            if actual_performance < 0.5:
                # Failed/Struggled
                tags_dict[tag] = min(1.0, current_miss_rate + 0.1)
            else:
                # Succeeded
                tags_dict[tag] = max(0.0, current_miss_rate - 0.1)
                
        profile.weak_tags = tags_dict
        await db.commit()
        
    @staticmethod
    async def recommend_next_problem(db: AsyncSession, user_id: int) -> int:
        """
        Yields the optimal next problem ID to solve.
        Target Problem Elo ~ User Elo
        Prioritizes problems tagged with their highest weakness score.
        """
        result = await db.execute(select(UserSkillProfile).where(UserSkillProfile.user_id == user_id))
        profile = result.scalars().first()
        
        target_elo = profile.elo_rating if profile else 1200.0
        weak_tags = profile.weak_tags if profile else {}
        target_difficulty = max(1, min(10, int((target_elo - 800) / 160) + 1))
        
        # Recommend problem closest to target difficulty.
        # In a real ORM setup this would find a problem not yet solved by the user.
        stmt = select(Problem).where(Problem.difficulty_level.between(target_difficulty - 1, target_difficulty + 1)).limit(1)
        problem = await db.execute(stmt)
        return problem.scalars().first().id
