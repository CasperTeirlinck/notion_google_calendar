import logging
import datetime as dt

from api_client.google import GCalendar
from api_client.notion import Notion
from common.utils import are_events_equivalent_notion, map_events_notion
from models.database import Database

logger = logging.getLogger(__name__)


def sync_database(notion: Notion, gcalendar: GCalendar, database: Database) -> None:
    """
    Sync dated notion pages for a single database to the specified Google Calendar.
    """

    logger.info(f"Starting to sync database {database.name}.")

    # Get events from Notion and Google Calendar
    events_notion = notion.get_events(database)
    events_google = gcalendar.get_events_notion(database)

    # Map events from Notion to events from Google Calendar
    events = map_events_notion(events_notion, events_google)

    # Create/Update/Delete events
    for event_notion, event_google in events:
        # Update event
        if event_notion and event_google:
            # Check if update is needed
            if are_events_equivalent_notion(event_notion, event_google):
                continue

            event_notion.google_event_id = event_google.google_event_id
            gcalendar.update_event_from_notion(event_notion)

        # Add event
        if event_notion and not event_google:
            # Dont create new events that are older that 5 days
            if event_notion.date.start < dt.datetime.now().replace(
                tzinfo=dt.timezone.utc
            ) - dt.timedelta(days=5):
                continue

            gcalendar.create_event_from_notion(event_notion)

        # Remove event
        if not event_notion and event_google:
            gcalendar.delete_event_notion(event_google)

    logger.info(f"Done syncing database {database.name}!")
