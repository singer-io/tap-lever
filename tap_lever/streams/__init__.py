from tap_lever.streams.applications import CandidateApplicationsStream
from tap_lever.streams.archive_reasons import ArchiveReasonsStream
from tap_lever.streams.candidates import CandidateStream
from tap_lever.streams.offers import CandidateOffersStream
from tap_lever.streams.postings import PostingsStream
from tap_lever.streams.referrals import CandidateReferralsStream
from tap_lever.streams.requisitions import RequisitionStream
from tap_lever.streams.sources import SourcesStream
from tap_lever.streams.stages import StagesStream
from tap_lever.streams.users import UsersStream

AVAILABLE_STREAMS = [
    CandidateStream,  # must sync first to fill CACHE
    ArchiveReasonsStream,
    CandidateApplicationsStream,
    CandidateOffersStream,
    CandidateReferralsStream,
    PostingsStream,
    RequisitionStream,
    SourcesStream,
    StagesStream,
    UsersStream,
]

__all__ = [
    "CandidateStream",
    "ArchiveReasonsStream",
    "CandidateApplicationsStream",
    "CandidateOffersStream",
    "CandidateReferralsStream",
    "PostingsStream",
    "RequisitionStream",
    "SourcesStream",
    "StagesStream",
    "UsersStream",
]
