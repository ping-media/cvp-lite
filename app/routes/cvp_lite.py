from fastapi import APIRouter, HTTPException, status
from typing import Dict, Any
import logging
from datetime import datetime
import uuid

from ..models import (
    Step1QuestionsRequest,
    Step1QuestionsResponse,
    Step1SubmitRequest,
    Step1SubmitResponse,
    Step1Insight,
    QuestionsRequest,
    QuestionsResponse,
    Question,
    QuestionOption,
    QuestionOptionTranslation,
    Assessment,
    AssessmentCategory,
    QuestionsMeta,
    QuestionsLinks,
)
from ..database import mongodb
from ..ai_service import ai_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/cvp_lite", tags=["cvp_lite"])


@router.post("/step1", response_model=Step1QuestionsResponse, status_code=status.HTTP_200_OK)
async def start_step1(request: Step1QuestionsRequest):
    """Start Step 1: Generate 10 adaptive MCQ questions for interests & strengths."""
    try:
        user = mongodb.get_user(request.student_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        # Prepare profile subset for question generation
        profile_subset: Dict[str, Any] = {
            "name": user.get("name"),
            "grade": user.get("grade"),
            "subject_stream": user.get("subject_stream"),
            "hobbies_and_passions": user.get("hobbies_and_passions", []),
            "dream_job": user.get("dream_job"),
            "city": user.get("city"),
            "country": user.get("country"),
        }

        data = ai_service.generate_step1_questions(profile_subset)
        questions = data.get("questions", [])

        message = (
            "Step 1: Interest & Strengths Discovery\n"
            "- Goal: Discover natural interests and emerging strengths\n"
            "- Time: 8-12 minutes\n"
            "- Framework: RIASEC + Multiple Intelligences\n"
            "Answer the following questions to reveal what genuinely excites and motivates you."
        )

        return Step1QuestionsResponse(student_id=request.student_id, questions=questions)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting Step 1: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.post("/step1/submit", response_model=Step1SubmitResponse, status_code=status.HTTP_200_OK)
async def submit_step1(request: Step1SubmitRequest):
    """Submit answers for Step 1; returns insights and advances current_step to 1."""
    try:
        user = mongodb.get_user(request.student_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        # Map answers to dict[question_id] = option_id for analysis
        answers_map: Dict[str, str] = {a.question_id: a.option_id for a in request.answers}

        profile_subset: Dict[str, Any] = {
            "name": user.get("name"),
            "grade": user.get("grade"),
            "subject_stream": user.get("subject_stream"),
            "hobbies_and_passions": user.get("hobbies_and_passions", []),
            "dream_job": user.get("dream_job"),
        }

        analysis = ai_service.analyze_step1_answers(profile_subset, answers_map)

        # Persist insights and mark step progress
        cvp = user.get("cvp_lite", {})
        cvp["step1"] = {
            "answers": request.answers,
            "insights": analysis,
        }
        cvp["current_step"] = max(1, int(cvp.get("current_step", 0) or 0))
        user["cvp_lite"] = cvp

        mongodb.create_or_update_user(user)

        message = (
            "Great work! We've analyzed your responses and discovered key interest themes and strengths.\n"
            "You'll use these insights in the next step of your CVP Lite journey."
        )

        return Step1SubmitResponse(
            student_id=request.student_id,
            insights=Step1Insight(
                summary=analysis.get("summary", ""),
                riasec_scores=analysis.get("riasec_scores"),
                mi_scores=analysis.get("mi_scores"),
                top_themes=analysis.get("top_themes"),
            ),
            message=message,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting Step 1: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.post("/questions", response_model=QuestionsResponse, status_code=status.HTTP_200_OK)
async def get_questions(request: QuestionsRequest):
    """Get static questions in the specified format for assessment."""
    try:
        # Static questions data
        questions = [
            Question(
                id="5d2f6f6a-3a3b-4c2b-9f0f-8e9b4f2f5b77",
                text="Which activity do you enjoy the most?",
                type="single_choice",
                options=[
                    QuestionOption(
                        id="opt1",
                        label="Building a model airplane",
                        label_translations=QuestionOptionTranslation(
                            hi="एक मॉडल हवाई जहाज बनाना",
                            en="Building a model airplane"
                        )
                    ),
                    QuestionOption(
                        id="opt2",
                        label="Solving a complex math problem",
                        label_translations=QuestionOptionTranslation(
                            hi="एक जटिल गणितीय समस्या हल करना",
                            en="Solving a complex math problem"
                        )
                    ),
                    QuestionOption(
                        id="opt3",
                        label="Organizing a charity event",
                        label_translations=QuestionOptionTranslation(
                            hi="एक चैरिटी कार्यक्रम का आयोजन करना",
                            en="Organizing a charity event"
                        )
                    ),
                    QuestionOption(
                        id="opt4",
                        label="Creating a piece of art",
                        label_translations=QuestionOptionTranslation(
                            hi="एक कला का टुकड़ा बनाना",
                            en="Creating a piece of art"
                        )
                    )
                ],
                required=True,
                category_id="riasec",
                weight=1.5,
                lang="en-IN",
                created_at="2025-08-21T07:15:00Z",
                order=1
            ),
            Question(
                id="9b0c1a27-9036-4a7a-ae78-0b4d2b6e2a11",
                text="Which role would you feel most comfortable in?",
                type="single_choice",
                options=[
                    QuestionOption(
                        id="k8JrQ2sM1fZb",
                        label="A researcher studying a new phenomenon",
                        label_translations=QuestionOptionTranslation(
                            hi="एक नया घटना अध्ययन करने वाला अध्यापक",
                            en="A researcher studying a new phenomenon"
                        )
                    ),
                    QuestionOption(
                        id="Wc3hL7r9QyP2",
                        label="A manager overseeing a team project",
                        label_translations=QuestionOptionTranslation(
                            hi="एक टीम पर अधिकारी",
                            en="A manager overseeing a team project"
                        )
                    ),
                    QuestionOption(
                        id="r2b7mK0Xn5Ta",
                        label="A counselor helping people overcome their problems",
                        label_translations=QuestionOptionTranslation(
                            hi="एक व्यक्ति को उनके समस्याओं को ओवरहेड करने वाला सलाहकार",
                            en="A counselor helping people overcome their problems"
                        )
                    ),
                    QuestionOption(
                        id="RANDOM_ID_12345",
                        label="A time traveler exploring unknown eras",
                        label_translations=QuestionOptionTranslation(
                            hi="एक समय यात्री जो अज्ञात युगों की खोज कर रहा है",
                            en="A time traveler exploring unknown eras"
                        )
                    )
                ],
                required=True,
                category_id="riasec",
                weight=1.5,
                lang="en-IN",
                created_at="2025-08-21T07:15:00Z",
                order=2
            )
        ]

        # Create assessment metadata
        categories = [
            AssessmentCategory(
                id="riasec",
                name="RIASEC Assessment",
                description="Holland's RIASEC model assessment",
                theory="Holland's RIASEC Model",
                weight=1.5
            ),
            AssessmentCategory(
                id="mi",
                name="Multiple Intelligences",
                description="Gardner's MI assessment",
                theory="Multiple Intelligences",
                weight=1.0
            )
        ]

        assessment = Assessment(
            id="a9f2d7f0-1e6a-4d9a-8b9e-8e6a1c8b9f22",
            step_type="interests_strengths",
            title="Interest & Strengths Discovery",
            scientific_basis="riasec",
            generated_at="2025-08-21T07:15:00Z",
            categories=categories
        )

        # Create meta information
        meta = QuestionsMeta(
            page=request.page,
            page_size=request.page_size,
            total=2,
            assessment=assessment
        )

        # Create links
        base_url = "https://api.example.com/v1/questions"
        links = QuestionsLinks(
            self=f"{base_url}?page=1&page_size=20",
            next=None,
            prev=None
        )

        return QuestionsResponse(
            data=questions,
            meta=meta,
            links=links
        )

    except Exception as e:
        logger.error(f"Error getting questions: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


