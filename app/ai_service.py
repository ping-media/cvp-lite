from openai import OpenAI
from typing import List, Dict, Any
from datetime import datetime
import logging
import random
from .config import settings

# Question generation policy and coverage requirements
QUESTION_SELECTION_CRITERIA: dict[str, str] = {
    "grade_adaptation": "Adjust complexity and scenarios to student's grade level",
    "cultural_relevance": "Use examples relevant to student's tier and country context",
    "interest_diversification": "Ensure coverage of all RIASEC domains",
    "randomization": "Prevent gaming by rotating question sets",
    "personalization": "Reference student's stated hobbies/interests where possible",
}

RIASEC_COVERAGE_REQUIRED: dict[str, int] = {
    "R": 2,  # Realistic
    "I": 2,  # Investigative
    "A": 2,  # Artistic
    "S": 2,  # Social
    "E": 1,  # Enterprising
    "C": 1,  # Conventional
}

logger = logging.getLogger(__name__)

class AIService:
    #AI Service class for generating personalized recipes using OpenAI GPT.Handles recipe generation, parsing, and fallback mechanisms.
    
    def __init__(self):
        #Initialize the AI service with OpenAI client. Sets up the OpenAI client using API key from settings.

        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)

    def generate_step1_questions(self, student_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Generate 10 adaptive MCQs (scenario-based) for Step 1 via GPT-4, return JSON.
        The JSON format will include id, prompt, options, scenario, and tags (optional).

        Selection criteria enforced:
        - Grade adaptation, cultural relevance (city/country), personalization (hobbies/dream_job)
        - Interest diversification across RIASEC with distribution: R=2, I=2, A=2, S=2, E=1, C=1
        - Randomization of final order to reduce gaming
        """
        try:
            grade_text = str(student_profile.get("grade") or "").strip()
            grade_lower = grade_text.lower()
            if any(x in grade_lower for x in ["plus two", "12th pass", "12 pass", "xii pass", "xii", "12th"]):
                grade_band = "post-12 (12th Pass)"
            elif any(x in grade_lower for x in ["grade 7", "class 7", " 7", " vii", "vii "]):
                grade_band = "middle school (Grade 7)"
            elif any(x in grade_lower for x in ["grade 8", "class 8", " 8", " viii", "viii "]):
                grade_band = "middle school (Grade 8)"
            elif any(x in grade_lower for x in ["grade 11", "class 11", " 11", " xi", "xi "]):
                grade_band = "senior secondary (Grade 11)"
            elif any(x in grade_lower for x in ["grade 12", "class 12", " 12"]):
                grade_band = "senior secondary (Grade 12)"
            elif any(x in grade_lower for x in ["grade 10", "class 10", " 10", " x", "x "]):
                grade_band = "secondary (Grade 10)"
            elif any(x in grade_lower for x in ["grade 9", "class 9", " 9", " ix", "ix "]):
                grade_band = "secondary (Grade 9)"
            else:
                grade_band = "unspecified"

            system_prompt = (
                "You are an assessment designer for students (Grades 7–12 and 12th Pass). "
                "Design exactly 10 adaptive, scenario-based MCQs to discover natural interests and strengths. "
                "Use Holland's RIASEC and Multiple Intelligences as implicit frameworks. "
                f"Student grade/class: {grade_text if grade_text else 'unknown'} (band: {grade_band}). "
                "Tailor language, scenarios, and difficulty by grade. Use culturally relevant examples for the student's city/country when provided. "
                "Embed light personalization referencing stated hobbies/interests or dream job when natural. "
                "Return STRICT JSON with an array 'questions'. Each item must include: \n"
                "- id (string)\n"
                "- prompt (one sentence)\n"
                "- options (array of 4 objects with fields id,text)\n"
                "- scenario (optional, short context)\n"
                "- tags (array) that MUST include exactly one of ['R','I','A','S','E','C'] to mark the primary RIASEC focus; you may include additional descriptors.\n"
                "Ensure the overall set follows this exact RIASEC distribution: R=2, I=2, A=2, S=2, E=1, C=1."
            )
            user_context = {
                "student_profile": {
                    "name": student_profile.get("name"),
                    "grade": student_profile.get("grade"),
                    "subject_stream": student_profile.get("subject_stream"),
                    "hobbies_and_passions": student_profile.get("hobbies_and_passions", []),
                    "dream_job": student_profile.get("dream_job"),
                    "city": student_profile.get("city"),
                    "country": student_profile.get("country"),
                }
            }

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Generate JSON questions for this student context: {user_context}"},
                {"role": "assistant", "content": "Return JSON ONLY with key 'questions'."},
            ]
            # Log final prompt/messages for observability
            try:
                logger.info(
                    "Step1 question generation prompt | model=%s | messages=%s",
                    settings.OPENAI_MODEL,
                    messages,
                )
            except Exception:
                # Do not block on logging issues
                pass

            response = self.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=messages,
                temperature=0.7,
                max_tokens=900,
            )

            import json, re
            text = response.choices[0].message.content
            match = re.search(r"\{[\s\S]*\}", text)
            data = json.loads(match.group(0)) if match else {"questions": []}

            # Normalize
            normalized = self._normalize_step1_questions(data.get("questions", []))
            # Enforce RIASEC distribution and ensure exactly 10 with random order
            desired = RIASEC_COVERAGE_REQUIRED
            normalized = self._enforce_riasec_distribution(normalized, desired, student_profile)
            random.shuffle(normalized)
            normalized = self._resequence_question_ids(normalized[:10])
            return {"questions": normalized}
        except Exception:
            # Fallback full question set (10)
            questions = self._enforce_riasec_distribution([], RIASEC_COVERAGE_REQUIRED, student_profile)
            random.shuffle(questions)
            questions = self._resequence_question_ids(questions[:10])
            return {"questions": questions}


    def analyze_step1_answers(self, student_profile: Dict[str, Any], answers: Dict[str, str]) -> Dict[str, Any]:
        """Analyze answers with GPT to produce insights and scores; returns JSON with insight fields."""
        try:
            system_prompt = (
                "You are a career guidance analyst. Given a student's brief profile and their MCQ selections, "
                "infer key interests and emerging strengths using RIASEC and Multiple Intelligences. "
                "Return STRICT JSON with keys: summary (string), riasec_scores (map of code->0..1), "
                "mi_scores (map), top_themes (string array)."
            )

            payload = {
                "profile": {
                    "name": student_profile.get("name"),
                    "grade": student_profile.get("grade"),
                    "stream": student_profile.get("subject_stream"),
                    "hobbies": student_profile.get("hobbies_and_passions", []),
                    "dream_job": student_profile.get("dream_job"),
                },
                "answers": answers,
            }

            response = self.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Analyze and return JSON only: {payload}"},
                ],
                temperature=0.4,
                max_tokens=700,
            )

            import json, re
            text = response.choices[0].message.content
            match = re.search(r"\{[\s\S]*\}", text)
            data = json.loads(match.group(0)) if match else {
                "summary": "Shows curiosity and emerging strengths in problem solving.",
                "riasec_scores": {"R": 0.2, "I": 0.7, "A": 0.4, "S": 0.5, "E": 0.3, "C": 0.6},
                "mi_scores": {"Logical": 0.7, "Linguistic": 0.5, "Bodily": 0.4},
                "top_themes": ["Curiosity", "Analytical", "Collaborative"],
            }
            return data
        except Exception:
            return {
                "summary": "Shows curiosity and emerging strengths in problem solving.",
                "riasec_scores": {"R": 0.2, "I": 0.7, "A": 0.4, "S": 0.5, "E": 0.3, "C": 0.6},
                "mi_scores": {"Logical": 0.7, "Linguistic": 0.5, "Bodily": 0.4},
                "top_themes": ["Curiosity", "Analytical", "Collaborative"],
            }

    def _normalize_step1_questions(self, questions: Any) -> list[dict]:
        """Ensure questions conform to expected shape and have ids/options with id/text."""
        normalized: list[dict] = []
        if not isinstance(questions, list):
            return normalized
        seen_ids: set[str] = set()
        counter = 1
        for q in questions:
            if not isinstance(q, dict):
                continue
            qid = str(q.get("id") or f"q{counter}").strip()
            if not qid or qid in seen_ids:
                # generate unique id
                while True:
                    qid = f"q{counter}"
                    counter += 1
                    if qid not in seen_ids:
                        break
            prompt = str(q.get("prompt") or q.get("question") or "").strip()
            options = q.get("options") or []
            norm_options = []
            if isinstance(options, list):
                for opt in options:
                    if not isinstance(opt, dict):
                        continue
                    oid = str(opt.get("id") or opt.get("key") or "").strip()
                    text = str(opt.get("text") or opt.get("label") or "").strip()
                    if oid and text:
                        norm_options.append({"id": oid, "text": text})
            item = {
                "id": qid,
                "prompt": prompt,
                "options": norm_options,
            }
            if q.get("scenario"):
                item["scenario"] = q["scenario"]
            if q.get("tags"):
                item["tags"] = q["tags"]
            seen_ids.add(qid)
            normalized.append(item)
        return normalized

    def _resequence_question_ids(self, questions: list[dict]) -> list[dict]:
        """Rename question ids sequentially as q1, q2, ... keeping the existing order."""
        resequenced: list[dict] = []
        for index, question in enumerate(questions, start=1):
            new_item = {**question, "id": f"q{index}"}
            resequenced.append(new_item)
        return resequenced

    def _extract_riasec_primary(self, tags: Any) -> str | None:
        """Extract the primary RIASEC code from tags if present."""
        if not tags or not isinstance(tags, list):
            return None
        riasec_set = {"R", "I", "A", "S", "E", "C", "Realistic", "Investigative", "Artistic", "Social", "Enterprising", "Conventional"}
        for tag in tags:
            if not isinstance(tag, str):
                continue
            t = tag.strip()
            # direct letter
            if t in {"R", "I", "A", "S", "E", "C"}:
                return t
            # full-word mapping
            mapping = {
                "Realistic": "R",
                "Investigative": "I",
                "Artistic": "A",
                "Social": "S",
                "Enterprising": "E",
                "Conventional": "C",
            }
            if t in mapping:
                return mapping[t]
        return None

    def _enforce_riasec_distribution(self, questions: list[dict], desired: dict[str, int], student_profile: Dict[str, Any]) -> list[dict]:
        """Select or synthesize questions to meet the desired RIASEC distribution.
        - Prefer model-generated questions first
        - Fill deficits from category fallback banks
        - Trim extras if any category exceeds its quota
        Always returns exactly sum(desired.values()) questions when possible.
        """
        total_needed = sum(desired.values())
        # Buckets from model output
        buckets: dict[str, list[dict]] = {k: [] for k in desired.keys()}
        for q in questions:
            primary = self._extract_riasec_primary(q.get("tags"))
            if primary in buckets:
                buckets[primary].append(q)
        # Start selection
        selected: list[dict] = []
        used_ids: set[str] = set()
        # Take up to desired count from each bucket
        for code, need in desired.items():
            take = buckets.get(code, [])[: need]
            for item in take:
                if item.get("id") in used_ids:
                    continue
                selected.append(item)
                used_ids.add(item.get("id", ""))
        # Fill deficits from fallback pools
        fallback_pools = self._fallback_by_riasec(student_profile)
        for code, need in desired.items():
            current = [q for q in selected if self._extract_riasec_primary(q.get("tags")) == code]
            deficit = need - len(current)
            if deficit <= 0:
                continue
            candidates = fallback_pools.get(code, [])
            for candidate in candidates:
                if deficit <= 0:
                    break
                cid = candidate.get("id")
                # ensure unique id
                new_id = cid
                suffix = 1
                while new_id in used_ids:
                    new_id = f"{cid}_{suffix}"
                    suffix += 1
                c = {**candidate, "id": new_id}
                selected.append(c)
                used_ids.add(new_id)
                deficit -= 1
        # If still short (should not happen), top up from any remaining fallback
        while len(selected) < total_needed:
            for code in ["R", "I", "A", "S", "E", "C"]:
                if len(selected) >= total_needed:
                    break
                for candidate in fallback_pools.get(code, []):
                    cid = candidate.get("id")
                    new_id = cid
                    suffix = 1
                    while new_id in used_ids:
                        new_id = f"{cid}_{suffix}"
                        suffix += 1
                    c = {**candidate, "id": new_id}
                    selected.append(c)
                    used_ids.add(new_id)
                    if len(selected) >= total_needed:
                        break
        # If overfull, trim by reducing categories that exceed desired counts first
        if len(selected) > total_needed:
            # Build category lists
            by_code: dict[str, list[int]] = {k: [] for k in desired.keys()}
            for idx, q in enumerate(selected):
                code = self._extract_riasec_primary(q.get("tags")) or ""
                if code in by_code:
                    by_code[code].append(idx)
            # Remove extras
            to_remove: set[int] = set()
            for code, need in desired.items():
                idxs = by_code.get(code, [])
                if len(idxs) > need:
                    # mark extras for removal (keep first 'need')
                    for drop_idx in idxs[need:]:
                        to_remove.add(drop_idx)
            selected = [q for i, q in enumerate(selected) if i not in to_remove]
        # Sanitize each question: ensure prompt string and exactly 4 valid options
        for q in selected:
            # prompt normalization
            q["prompt"] = str(q.get("prompt") or q.get("question") or "").strip()
            # scenario normalization if present
            if "scenario" in q and not isinstance(q.get("scenario"), str):
                q.pop("scenario", None)
            # options normalization
            q["options"] = self._sanitize_options(q.get("options"))
        return selected[:total_needed]

    def _sanitize_options(self, options: Any) -> list[dict]:
        """Ensure options is a list of exactly 4 entries with id and text.
        If incoming options are malformed or fewer than 2 valid ones, replace with Likert defaults.
        """
        valid: list[dict] = []
        if isinstance(options, list):
            for opt in options:
                if not isinstance(opt, dict):
                    continue
                oid = str(opt.get("id") or opt.get("key") or "").strip()
                text = str(opt.get("text") or opt.get("label") or "").strip()
                if oid and text:
                    valid.append({"id": oid, "text": text})
        if len(valid) < 2:
            return [
                {"id": "a", "text": "Sounds exactly like me"},
                {"id": "b", "text": "Somewhat like me"},
                {"id": "c", "text": "A little like me"},
                {"id": "d", "text": "Not like me"},
            ]
        # Truncate or pad to 4
        valid = valid[:4]
        # If fewer than 4, append generic options with unique ids
        ids = {v["id"] for v in valid}
        fallback_stream = [
            ("a", "Sounds exactly like me"),
            ("b", "Somewhat like me"),
            ("c", "A little like me"),
            ("d", "Not like me"),
        ]
        for oid, text in fallback_stream:
            if len(valid) >= 4:
                break
            if oid in ids:
                continue
            valid.append({"id": oid, "text": text})
            ids.add(oid)
        return valid

    def _fallback_by_riasec(self, student_profile: Dict[str, Any]) -> dict[str, list[dict]]:
        """Provide small question pools keyed by RIASEC code to satisfy coverage when the model output is insufficient."""
        name = (student_profile or {}).get("name") or "you"
        dream_job = (student_profile or {}).get("dream_job") or "a role you aspire to"
        hobbies = (student_profile or {}).get("hobbies_and_passions") or []
        hobby = hobbies[0] if hobbies else "your favorite activity"
        pools: dict[str, list[dict]] = {
            "R": [
                {
                    "id": "R1",
                    "prompt": "You have access to a maker lab for an hour. What would you most like to do?",
                    "scenario": "School makerspace hour",
                    "options": [
                        {"id": "a", "text": "Build or fix a simple device using tools"},
                        {"id": "b", "text": "Sketch ideas for a future project"},
                        {"id": "c", "text": "Plan tasks and assign roles"},
                        {"id": "d", "text": "Research best practices before starting"},
                    ],
                    "tags": ["R"],
                },
                {
                    "id": "R2",
                    "prompt": "Which weekend plan sounds most fun to you?",
                    "options": [
                        {"id": "a", "text": "Do a hands-on activity like biking, hiking, or fixing something"},
                        {"id": "b", "text": "Write or create digital art"},
                        {"id": "c", "text": "Lead a community game or event"},
                        {"id": "d", "text": "Study an interesting topic online"},
                    ],
                    "tags": ["R"],
                },
            ],
            "I": [
                {
                    "id": "I1",
                    "prompt": "You notice a pattern in how your classmates learn. What do you do next?",
                    "options": [
                        {"id": "a", "text": "Design an experiment to test your idea"},
                        {"id": "b", "text": "Share a motivational story with the class"},
                        {"id": "c", "text": "Create a poster to explain it visually"},
                        {"id": "d", "text": "Coordinate a study group"},
                    ],
                    "tags": ["I"],
                },
                {
                    "id": "I2",
                    "prompt": "A device at an event stops working. What is your first step?",
                    "scenario": "Live school event",
                    "options": [
                        {"id": "a", "text": "Diagnose the root cause step by step"},
                        {"id": "b", "text": "Announce a quick plan and delegate"},
                        {"id": "c", "text": "Document the incident and adjust the schedule"},
                        {"id": "d", "text": "Improvise a creative workaround"},
                    ],
                    "tags": ["I"],
                },
            ],
            "A": [
                {
                    "id": "A1",
                    "prompt": f"You are creating something related to {hobby}. Which approach excites you most?",
                    "options": [
                        {"id": "a", "text": "Try a bold, original style"},
                        {"id": "b", "text": "Follow a proven template"},
                        {"id": "c", "text": "Gather data to inform the design"},
                        {"id": "d", "text": "Organize a team to produce it"},
                    ],
                    "tags": ["A"],
                },
                {
                    "id": "A2",
                    "prompt": "In a group project, which role do you pick?",
                    "options": [
                        {"id": "a", "text": "Designer who makes it creative"},
                        {"id": "b", "text": "Leader who coordinates tasks"},
                        {"id": "c", "text": "Researcher who digs into facts"},
                        {"id": "d", "text": "Organizer who tracks progress"},
                    ],
                    "tags": ["A"],
                },
            ],
            "S": [
                {
                    "id": "S1",
                    "prompt": "A friend struggles to understand a topic you like. What do you do?",
                    "options": [
                        {"id": "a", "text": "Explain it with simple examples"},
                        {"id": "b", "text": "Create a visual guide"},
                        {"id": "c", "text": "Assign practice tasks"},
                        {"id": "d", "text": "Research more before responding"},
                    ],
                    "tags": ["S"],
                },
                {
                    "id": "S2",
                    "prompt": "At a community event, which activity draws you in?",
                    "options": [
                        {"id": "a", "text": "Helping visitors and answering questions"},
                        {"id": "b", "text": "Designing posters or visuals"},
                        {"id": "c", "text": "Analyzing feedback data"},
                        {"id": "d", "text": "Operating equipment"},
                    ],
                    "tags": ["S"],
                },
            ],
            "E": [
                {
                    "id": "E1",
                    "prompt": f"You want to start a small initiative at school around {hobby}. What is your first move?",
                    "options": [
                        {"id": "a", "text": "Pitch the idea and inspire a team"},
                        {"id": "b", "text": "Design a logo and theme"},
                        {"id": "c", "text": "Draft a detailed timeline"},
                        {"id": "d", "text": "Research similar initiatives"},
                    ],
                    "tags": ["E"],
                },
                {
                    "id": "E2",
                    "prompt": f"If you were leading a club related to {dream_job}, what would you focus on first?",
                    "options": [
                        {"id": "a", "text": "Build excitement and recruit members"},
                        {"id": "b", "text": "Create visuals and publicity"},
                        {"id": "c", "text": "Set up processes and roles"},
                        {"id": "d", "text": "Collect data on member interests"},
                    ],
                    "tags": ["E"],
                },
            ],
            "C": [
                {
                    "id": "C1",
                    "prompt": "When planning a class event, which task do you enjoy most?",
                    "options": [
                        {"id": "a", "text": "Organizing schedules and checklists"},
                        {"id": "b", "text": "Creating posters and themes"},
                        {"id": "c", "text": "Testing and reviewing equipment"},
                        {"id": "d", "text": "Giving a motivating speech"},
                    ],
                    "tags": ["C"],
                },
                {
                    "id": "C2",
                    "prompt": "You are assigned to document a project. What do you do first?",
                    "options": [
                        {"id": "a", "text": "Create a clear template and file structure"},
                        {"id": "b", "text": "Design a cover page"},
                        {"id": "c", "text": "Interview team members"},
                        {"id": "d", "text": "Run a test of the final product"},
                    ],
                    "tags": ["C"],
                },
            ],
        }
        return pools

    def _fallback_step1_question_bank(self, student_profile: Dict[str, Any]) -> list[dict]:
        """Return 10 scenario-based MCQs covering RIASEC and MI as a reliable fallback."""
        name = (student_profile or {}).get("name") or "you"
        questions: list[dict] = [
            {
                "id": "q1",
                "prompt": "You have a free afternoon at school. Which activity excites you most?",
                "scenario": "School club hour",
                "options": [
                    {"id": "a", "text": "Build a small robot with a kit"},  # R/I
                    {"id": "b", "text": "Write a short story or poem"},      # A
                    {"id": "c", "text": "Organize a fun event for classmates"}, # E/S
                    {"id": "d", "text": "Practice a new sport or dance routine"} # R/Bodily
                ],
                "tags": ["R", "I", "A", "E", "S", "Bodily-Kinesthetic"],
            },
            {
                "id": "q2",
                "prompt": "In a group project, which role do you naturally take?",
                "scenario": "Team assignment",
                "options": [
                    {"id": "a", "text": "Team leader who coordinates tasks"},      # E/C
                    {"id": "b", "text": "Researcher who digs into facts"},        # I
                    {"id": "c", "text": "Designer who makes it creative"},        # A
                    {"id": "d", "text": "Organizer who keeps everything on track"} # C
                ],
                "tags": ["E", "I", "A", "C"],
            },
            {
                "id": "q3",
                "prompt": "Which challenge would you most enjoy solving?",
                "options": [
                    {"id": "a", "text": "Build a device that solves a real problem"}, # R/I
                    {"id": "b", "text": "Analyze clues to solve a mystery"},         # I
                    {"id": "c", "text": "Create a campaign to inspire others"},      # A/E/S
                    {"id": "d", "text": "Help classmates resolve a conflict"}        # S
                ],
                "tags": ["R", "I", "A", "E", "S"],
            },
            {
                "id": "q4",
                "prompt": "Which class activity sounds the most exciting to you?",
                "options": [
                    {"id": "a", "text": "Run an experiment in the lab"},            # R/I
                    {"id": "b", "text": "Debate a social issue"},                   # S/E
                    {"id": "c", "text": "Design a simple mobile app"},             # I/A
                    {"id": "d", "text": "Plan and organize a school event"}        # E/C
                ],
                "tags": ["R", "I", "S", "E", "A", "C"],
            },
            {
                "id": "q5",
                "prompt": "What kind of feedback do people often give you?",
                "options": [
                    {"id": "a", "text": "You explain things clearly"},              # S/Linguistic
                    {"id": "b", "text": "You come up with creative ideas"},         # A
                    {"id": "c", "text": "You get things done and deliver"},         # C/E
                    {"id": "d", "text": "You notice patterns and details quickly"} # I
                ],
                "tags": ["S", "A", "C", "E", "I"],
            },
            {
                "id": "q6",
                "prompt": "If you could join any new club this term, which would you pick?",
                "options": [
                    {"id": "a", "text": "Robotics or coding club"},                # I/R
                    {"id": "b", "text": "Drama, music, or art club"},              # A
                    {"id": "c", "text": "Entrepreneurship/Business club"},        # E
                    {"id": "d", "text": "Eco-volunteering or peer mentoring"}     # S
                ],
                "tags": ["I", "R", "A", "E", "S"],
            },
            {
                "id": "q7",
                "prompt": "Which weekend plan sounds most fun to you?",
                "options": [
                    {"id": "a", "text": "Visit a science fair or museum"},         # I
                    {"id": "b", "text": "Write music or make a short film"},       # A
                    {"id": "c", "text": "Play a sport or go hiking"},              # R/Bodily
                    {"id": "d", "text": "Attend a community event and meet people"} # S/E
                ],
                "tags": ["I", "A", "R", "S", "E"],
            },
            {
                "id": "q8",
                "prompt": "During a school event, a device suddenly stops working. What do you do first?",
                "scenario": "Live event issue",
                "options": [
                    {"id": "a", "text": "Diagnose the root cause and test components"}, # R/I
                    {"id": "b", "text": "Rally the team and delegate quick tasks"},     # E/S
                    {"id": "c", "text": "Re-route the process and document changes"},   # C
                    {"id": "d", "text": "Create a clever workaround on the spot"}      # A
                ],
                "tags": ["R", "I", "E", "S", "C", "A"],
            },
            {
                "id": "q9",
                "prompt": "Which activity makes you forget the time when you get into it?",
                "options": [
                    {"id": "a", "text": "Coding, puzzles, or science experiments"}, # I
                    {"id": "b", "text": "Drawing, design, or composing music"},     # A
                    {"id": "c", "text": "Playing sports or practicing choreography"},# R/Bodily
                    {"id": "d", "text": "Helping a friend understand a topic"}      # S
                ],
                "tags": ["I", "A", "R", "S"],
            },
            {
                "id": "q10",
                "prompt": "When faced with a problem, what’s your preferred approach?",
                "options": [
                    {"id": "a", "text": "Hands-on building and testing"},          # R
                    {"id": "b", "text": "Research, analyze, and reason it out"},  # I/Logical
                    {"id": "c", "text": "Brainstorm creative stories or visuals"}, # A
                    {"id": "d", "text": "Plan, coordinate, and track progress"}    # C/E
                ],
                "tags": ["R", "I", "A", "C", "E"],
            },
        ]
        return questions

    def generate_recipe(self, user_profile: Dict[str, Any], similar_recipes: List[Dict[str, Any]]) -> Dict[str, Any]:
        #Generate a personalized recipe using OpenAI GPT based on user preferences and similar recipes.
        
        #Args: user_profile (Dict[str, Any]): User's profile containing preferences, dietary restrictions, etc.
        #similar_recipes (List[Dict[str, Any]]): List of similar recipes for inspiration
            
        #Returns: Dict[str, Any]: Generated recipe with all required fields including image_prompt
            
        #Raises: Exception: If recipe generation fails, returns fallback recipe
        
        try:
            # Create context from user profile and similar recipes
            context = self._create_context(user_profile, similar_recipes)
            
            # Log the final prompt being sent to OpenAI
            final_prompt = f"Generate a personalized recipe based on this context: {context}"
            logger.info(f"Final prompt sent to OpenAI: {final_prompt}")
            
            # Generate recipe using OpenAI GPT model
            response = self.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": """You are a professional chef and recipe creator with extensive culinary expertise. Generate personalized recipes based on user preferences and similar recipes.

IMPORTANT: You must return a valid JSON object with ALL the following fields:
{
    "recipe_name": "Simple descriptive name",
    "ingredients": ["ingredient1", "ingredient2", ...],
    "instructions": ["step1", "step2", ...],
    "cooking_time": "X minutes",
    "difficulty": "Easy/Medium/Hard",
    "servings": 4,
    "serving_size": "1 cup/200g/1 piece",
    "dietary_tags": ["vegetarian", "gluten-free", etc.],
    "nutritional_facts": {
        "calories": 350,
        "protein": "15g",
        "carbohydrates": "45g",
        "fat": "12g",
        "fiber": "8g",
        "sugar": "5g",
        "sodium": "400mg"
    },
    "image_prompt": "Detailed visual description for generating recipe image - describe the final dish appearance, plating, colors, and presentation"
}

Guidelines for better recipe creation:
- Consider user's dietary preferences and restrictions
- Use ingredients that complement the user's favorite foods
- Create balanced, nutritious recipes with proper macro distribution
- Provide clear, step-by-step instructions
- Ensure cooking time is realistic
- Make the image_prompt detailed and appetizing
- Consider seasonal ingredients and cooking techniques
- Adapt recipes based on similar recipe inspirations provided
- Calculate accurate nutritional facts per serving
- Specify clear serving size (e.g., "1 cup", "200g", "1 piece")
- Ensure nutritional facts are realistic and balanced
- Consider dietary restrictions when calculating macros"""
                    },
                    {
                        "role": "user",
                        "content": f"Generate a personalized recipe based on this context: {context}"
                    }
                ],
                temperature=0.8,  # Slightly higher creativity for better recipe variety
                max_tokens=1500   # More tokens for detailed recipes and instructions
            )
            
            # Parse the response
            recipe_text = response.choices[0].message.content
            recipe_data = self._parse_recipe_response(recipe_text)
            
            # Generate image URL using the image prompt
            image_prompt = recipe_data.get("image_prompt", "")
            # image_url = self._generate_recipe_image(image_prompt)
            image_url = ""
            
            # Add the generated image URL only if it's not empty
            if image_url:
                recipe_data["image_url"] = image_url
            else:
                recipe_data["image_url"] = ""
            
            # Add metadata
            recipe_data["user_id"] = user_profile["student_id"]
            recipe_data["generated_at"] = datetime.utcnow()
            
            return recipe_data
            
        except Exception as e:
            return self._get_fallback_recipe(user_profile)
    
    def _create_context(self, user_profile: Dict[str, Any], similar_recipes: List[Dict[str, Any]]) -> str:
        """Create context string for recipe generation"""
        context_parts = []
        
        # User preferences - extract only one favorite food and dietary preferences
        favorite_foods = user_profile.get('favorite_foods', [])
        if favorite_foods:
            # Randomly select one favorite food item for recipe generation
            primary_food = random.choice(favorite_foods)
            context_parts.append(f"User's primary favorite food: {primary_food}")
        else:
            context_parts.append("User's favorite foods: Not specified")
        
        if user_profile.get('dietary_preferences'):
            context_parts.append(f"Dietary preferences: {', '.join(user_profile['dietary_preferences'])}")
        
        # Similar recipes for inspiration - only include highly relevant ones
        if similar_recipes:
            relevant_recipes = []
            for recipe in similar_recipes:
                score = recipe.get('score', 0)
                # Only include recipes with high similarity score (>0.8)
                if score > 0.8:
                    recipe_info = recipe.get('metadata', {})
                    relevant_recipes.append(f"{recipe_info.get('name', 'Unknown')} - {recipe_info.get('cuisine', 'Unknown cuisine')}")
            
            if relevant_recipes:
                context_parts.append("Similar recipes for inspiration:")
                # Only include the most relevant recipe
                context_parts.append(f"1. {relevant_recipes[0]}")
            else:
                context_parts.append("No highly relevant recipes found for inspiration.")
        
        return "\n".join(context_parts)
    
    def _generate_recipe_image(self, image_prompt: str) -> str:
        """
        Generate an image URL using OpenAI's DALL-E model based on the image prompt.
        
        Args:
            image_prompt (str): Detailed description of the dish to generate
            
        Returns:
            str: URL of the generated image, or empty string if generation fails
        """
        try:
            # Generate image using DALL-E
            response = self.client.images.generate(
                model="dall-e-3",  # Use DALL-E 3 for high quality images
                prompt=image_prompt,
                size="1024x1024",  # Standard size for recipe images
                quality="standard",
                n=1  # Generate one image
            )
            
            # Extract the image URL from the response
            if response.data and len(response.data) > 0:
                image_url = response.data[0].url
                return image_url
            else:
                return ""
            
        except Exception as e:
            return ""  # Return empty string if image generation fails
    
    def _parse_recipe_response(self, response_text: str) -> Dict[str, Any]:
        """Parse OpenAI response into structured recipe data"""
        try:
            # Try to extract JSON from the response
            import json
            import re
            
            # Find JSON-like content
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                recipe_json = json.loads(json_match.group())
                
                # Ensure image_prompt is present
                if 'image_prompt' not in recipe_json:
                    recipe_name = recipe_json.get('recipe_name', 'Recipe')
                    recipe_json['image_prompt'] = f"A delicious {recipe_name.lower()} served on a plate with garnishes"
                
                # Ensure serving_size is present
                if 'serving_size' not in recipe_json:
                    recipe_json['serving_size'] = "1 serving"
                
                # Ensure nutritional_facts is present
                if 'nutritional_facts' not in recipe_json:
                    recipe_json['nutritional_facts'] = {
                        "calories": 300,
                        "protein": "10g",
                        "carbohydrates": "40g",
                        "fat": "10g",
                        "fiber": "5g",
                        "sugar": "3g",
                        "sodium": "300mg"
                    }
                
                return recipe_json
            else:
                # Fallback parsing
                return self._fallback_parse(response_text)
                
        except Exception as e:
            return self._get_default_recipe()
    
    def _fallback_parse(self, text: str) -> Dict[str, Any]:
        """Fallback parsing for non-JSON responses"""
        # Simple parsing for common patterns
        lines = text.split('\n')
        recipe_data = {
            "recipe_name": "Simple Recipe",
            "ingredients": [],
            "instructions": [],
            "cooking_time": "30 minutes",
            "difficulty": "Medium",
            "servings": 4,
            "serving_size": "1 serving",
            "dietary_tags": [],
            "nutritional_facts": {
                "calories": 300,
                "protein": "10g",
                "carbohydrates": "40g",
                "fat": "10g",
                "fiber": "5g",
                "sugar": "3g",
                "sodium": "300mg"
            },
            "image_prompt": "A delicious homemade dish served on a plate"
        }
        
        for line in lines:
            line = line.strip()
            if line.startswith("Ingredients:"):
                # Parse ingredients
                pass
            elif line.startswith("Instructions:"):
                # Parse instructions
                pass
            elif "ingredients" in line.lower():
                # Extract ingredients
                pass
        
        return recipe_data
    
    def _get_fallback_recipe(self, user_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a fallback recipe when AI generation fails"""
        # Generate fallback recipe structure
        favorite_foods = user_profile.get('favorite_foods', [])
        primary_food = random.choice(favorite_foods) if favorite_foods else 'Recipe'
        
        fallback_recipe = {
            "recipe_name": f"Simple {primary_food}",
            "ingredients": ["ingredient1", "ingredient2", "ingredient3"],
            "instructions": [
                "Step 1: Prepare ingredients",
                "Step 2: Cook according to preference",
                "Step 3: Serve and enjoy"
            ],
            "cooking_time": "30 minutes",
            "difficulty": "Medium",
            "servings": 4,
            "serving_size": "1 serving",
            "dietary_tags": user_profile.get('dietary_preferences', []),
            "nutritional_facts": {
                "calories": 350,
                "protein": "12g",
                "carbohydrates": "45g",
                "fat": "12g",
                "fiber": "6g",
                "sugar": "4g",
                "sodium": "350mg"
            },
            "image_prompt": f"A delicious {primary_food} served on a plate",
            "user_id": user_profile["student_id"],
            "generated_at": datetime.utcnow()
        }
        
        # Try to generate image for fallback recipe
        try:
            image_url = self._generate_recipe_image(fallback_recipe["image_prompt"])
            fallback_recipe["image_url"] = image_url
        except Exception as e:
            fallback_recipe["image_url"] = ""
        
        return fallback_recipe
    
    def _get_default_recipe(self) -> Dict[str, Any]:
        """Get a default recipe structure"""
        # Generate default recipe structure
        default_recipe = {
            "recipe_name": "Simple Pasta",
            "ingredients": ["pasta", "olive oil", "garlic", "herbs", "salt"],
            "instructions": [
                "Boil pasta according to package instructions",
                "Heat olive oil in a pan",
                "Add garlic and herbs",
                "Combine with pasta and serve"
            ],
            "cooking_time": "20 minutes",
            "difficulty": "Easy",
            "servings": 2,
            "serving_size": "1 cup",
            "dietary_tags": ["vegetarian"],
            "nutritional_facts": {
                "calories": 320,
                "protein": "8g",
                "carbohydrates": "55g",
                "fat": "8g",
                "fiber": "3g",
                "sugar": "2g",
                "sodium": "250mg"
            },
            "image_prompt": "A simple pasta dish with olive oil, garlic, and herbs served on a white plate",
            "generated_at": datetime.utcnow()
        }
        
        # Try to generate image for default recipe
        try:
            image_url = self._generate_recipe_image(default_recipe["image_prompt"])
            default_recipe["image_url"] = image_url
        except Exception as e:
            default_recipe["image_url"] = ""
        
        return default_recipe

# Create global AI service instance
ai_service = AIService() 