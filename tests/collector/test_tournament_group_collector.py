"""
Test script for the GroupBatchProcessor.

This script demonstrates how to use the GroupBatchProcessor to batch process
multiple tournament groups in NIKKE.
"""
import logging

from collector.tournament_group_collector import GroupDataCollector
from tests.collector.utils import keyboard_terminable

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@keyboard_terminable()
def test_tournament_group_collector(group_collector: GroupDataCollector):
    group_collector.collect_groups(group_numbers=[1, 2])
