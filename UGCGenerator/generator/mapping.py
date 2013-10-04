import sys
sys.path.append('/Users/javier.hernandez/wip/UGCBuilder')
from generator import scf_feed_builder

def column_mapping():
	'''
		this list defines the order of the columns in the import file
	'''
	column_map = [
		'ProductId',
		'ReviewId',
		'OverallRating', 
		'ReviewTitle',
		'ReviewSummary',
		'SubmissionDate',
		'ReviewerName', 
		'ReviewerId'
		'BadgeId'
	]

	return column_map