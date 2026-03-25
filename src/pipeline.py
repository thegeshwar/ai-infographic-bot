"""Main pipeline orchestrator."""

import asyncio
import logging

from src.discover import discover_stories
from src.curate import curate_stories
from src.generate import generate_infographic
from src.history import is_posted, record_post
from src.notify import send_notification
from src.post import post_to_twitter, post_to_linkedin

logger = logging.getLogger(__name__)


def run_pipeline(stages: list[str] | None = None):
    """Run the full pipeline or specific stages."""
    stages = stages or ["discover", "curate", "generate", "post"]

    stories = []
    curated = []
    image_path = None

    try:
        if "discover" in stages:
            logger.info("=== Stage: Discover ===")
            stories = discover_stories()
            logger.info(f"Found {len(stories)} stories")

        if "curate" in stages:
            logger.info("=== Stage: Curate ===")
            if not stories:
                stories = discover_stories()
            curated = curate_stories(stories)
            logger.info(f"Curated {len(curated)} stories")

        if "generate" in stages:
            logger.info("=== Stage: Generate ===")
            if not curated:
                if not stories:
                    stories = discover_stories()
                curated = curate_stories(stories)

            # Filter out already-posted stories
            new_curated = [s for s in curated if not is_posted(s.get("url", ""))]
            if not new_curated:
                logger.info("All stories already posted — skipping generation")
            else:
                curated = new_curated
            image_path = generate_infographic(curated)
            logger.info(f"Generated infographic: {image_path}")

        if "post" in stages:
            logger.info("=== Stage: Post ===")
            if not image_path:
                logger.error("No image to post — run generate stage first")
                return
            caption = _build_caption(curated)
            asyncio.run(_post_all(image_path, caption, curated))

        logger.info("Pipeline complete")
        send_notification(
            "AI Infographic Bot",
            f"Pipeline completed successfully. Stages: {', '.join(stages)}",
            level="info",
        )

    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        send_notification(
            "AI Infographic Bot — ERROR",
            f"Pipeline failed: {e}",
            level="error",
        )


def _build_caption(curated: list[dict]) -> str:
    """Build a social media caption from curated stories."""
    lines = ["🤖 AI/ML Daily Digest\n"]
    for story in curated:
        lines.append(f"▸ {story['headline']}")
    lines.append("\n#AI #MachineLearning #Tech #AINews")
    return "\n".join(lines)


async def _post_all(image_path, caption: str, curated: list[dict] | None = None):
    """Post to all configured platforms."""
    results = await asyncio.gather(
        post_to_twitter(image_path, caption),
        post_to_linkedin(image_path, caption),
        return_exceptions=True,
    )
    for platform, result in zip(["Twitter", "LinkedIn"], results):
        if isinstance(result, Exception):
            logger.error(f"{platform} failed: {result}")
        elif result:
            logger.info(f"{platform}: posted successfully")
            # Record successful posts to history
            if curated:
                for story in curated:
                    record_post(story, platform.lower(), str(image_path))
        else:
            logger.info(f"{platform}: skipped (not configured)")
