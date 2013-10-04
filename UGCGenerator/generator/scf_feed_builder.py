#! /usr/bin/env python
import time, sys, csv, re, datetime, string, random, subprocess
import math
#sys.path.append('/Users/javier.hernandez/wip/UGCBuilder')
#from generator import mapping
from xml.etree.ElementTree import *
from optparse import OptionParser



###################################################################
# Nuts and bolts
###################################################################
column_map = [
	'ReviewId',
	'SubmissionDate',
	'OverallRating',
	'Traction',
	'Durability', 
	'Comfort', 
	'ReviewerName', 
	'ReviewerId',
	'ReviewTitle',
	'ReviewSummary',
	'IPAddress',
	'TireMake',
	'TireModel',
	'VehicleYear',
	'VehicleMake',
	'ProductId'
]
secondaryRatings = [
	'Traction', 
	'Durability', 
	'Comfort'
]

def populateTags(parentTag, tagTitle, tagText):
	node = SubElement(parentTag, tagTitle)
	node.text = tagText

def parseLine(line, reviewDict, errorFile):

	validColumns = True

	for column in column_map:
		try: 
			reviewDict[column] = re.sub('\n\t', ' ', line[column_map.index(column)].encode('utf-8'))
		except UnicodeDecodeError:
			line.append('UnicodeError')
			errorFile.write(string.join(line, '\t') + '\n')
			validColumns = False
	
	if not validColumns: 
		reviewDict = {}

	return reviewDict

def roundRating(rawRating):

	decimalValue = math.modf(rawRating)[0]

	if rawRating == 0:
		roundedRating = 0
		#print '\n== 0: ' + 'raw: ' + str(rawRating) + '\trounded: ' + str(roundedRating)
	elif rawRating <= 1.0:
		roundedRating = 1.0
		#print '\n< 1, not 0: ' + 'raw: ' + str(rawRating) + '\trounded: ' + str(roundedRating)
	elif decimalValue >= .5:
		roundedRating = math.ceil(rawRating)
		#print '\ndec val >=.5: ' + str(decimalValue) + '\t raw: ' + str(rawRating) + '\trounded: ' + str(roundedRating)
	else:
		roundedRating = math.floor(rawRating)
		#print '\ndec val < 5: ' + str(decimalValue) + '\t raw: ' + str(rawRating) + '\t rounded: ' + str(roundedRating)

	return str(int(roundedRating))
		
def generateFeed(options):
	# Access files
	clientFile = open(options.input)
	clientProductFeed = open(options.output, 'w')
	errorFile = open('error.log', 'w')
	reader = csv.reader(clientFile, delimiter="|")

	# Define Feed tag values
	generateDateTime = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())
	namespace = 'http://www.bazaarvoice.com/xs/PRR/StandardClientFeed/' + options.schema

	# Build necessary header
	xmlPrefix = "<?xml version='1.0' encoding='UTF-8'?>"
	root = Element('Feed')
	root.set('name', options.clientName)
	root.set('xmlns', namespace)
	root.set('extractDate', generateDateTime)

	#nuts and bolts
	unique_id = random.randint(10000000,99999999) * random.randint(10000000,99999999)
	products = []
	reviews = {}

	# Loop through input, assuming first line is header
	reader.next() 

	for line in reader:
		_review = {}
		_review = parseLine(line, _review, errorFile)

		if not _review.keys():
			continue
		if _review['ProductId'] == '#N/A':
			line.append('ProductID Error')
			errorFile.write(string.join(line, '\t') + '\n')
			continue
		elif _review['OverallRating'] == '0':
			line.append('OverallRating is 0')
			errorFile.write(string.join(line, '\t') + '\n')
		elif _review['ProductId'] not in reviews:
			reviews[_review['ProductId']] = []
			reviews[_review['ProductId']].append(_review)
		else:
			reviews[_review['ProductId']].append(_review)

	for product_id in reviews.keys():
	 	productNode = SubElement(root, 'Product')
	 	productNode.set('id', product_id)
	
	 	externalIDNode = SubElement(productNode, 'ExternalId')
	 	externalIDNode.text = product_id

	  	reviewsNode = SubElement(productNode, 'Reviews')

		for review in reviews[product_id]:
		
	 		rNode = SubElement(reviewsNode, 'Review')
	 		rNode.set('id', review['ReviewId'])
			
			#Review Text
			if review['ReviewTitle']: 
				titleNode = SubElement(rNode, 'Title')
				titleNode.text = review['ReviewTitle']

			if review['ReviewSummary']:
				summaryNode = SubElement(rNode, 'ReviewText')
				summaryNode.text = review['ReviewSummary']
				
			#ratings
			if review['OverallRating']:
				ratingNode = SubElement(rNode, 'Rating')
				#print '\n==overall=='
				ratingNode.text = roundRating(float(review['OverallRating']))

			ratingsOnlyNode = SubElement(rNode, 'RatingsOnly')

			if review['ReviewSummary'] or review['ReviewSummary']:
				ratingsOnlyNode.text = 'false'
			else:
				ratingsOnlyNode.text = 'true'

			#secondary ratings
			ratingsValueNode = SubElement(rNode, 'RatingValues')

			for secRating in secondaryRatings:
				
				#print '==secondary ratings==' + secRating + 'rating: ' + review[secRating]

				if roundRating(float(review[secRating])) != '0': 
					#print 'proceed with rounding and adding to ratings'

					rvNode = SubElement(ratingsValueNode, 'RatingValue')

					rvRatingsNode = SubElement(rvNode, 'Rating')
					rvRatingsNode.text = roundRating(float(review[secRating]))

					rvDimensionNode = SubElement(rvNode, 'RatingDimension')
					rvDimensionNode.set('id', secRating)
					rvDimensionNode.set('displayType', 'NORMAL')
					rvDimensionNode.set('selectedValueInDisplayEnabled', 'false')

					rvDimExtIdNode = SubElement(rvDimensionNode, 'ExternalId')
					rvDimExtIdNode.text = secRating

					rvDimRangeNode = SubElement(rvDimensionNode, 'RatingRange')
					rvDimRangeNode.text = '5'

					rvDimLabelNode = SubElement(rvDimensionNode, 'Label')
					rvDimLabelNode.text = secRating

					rvDimLabel1Node = SubElement(rvDimensionNode, 'Label1')
					rvDimLabel1Node.text = secRating

			if review['VehicleMake'] and review['VehicleYear']:
				tagsNode = SubElement(rNode, 'Tags')
				
				yearDimensionNode = SubElement(tagsNode, 'TagDimension')
				yearDimensionNode.set('id', 'Year')
				yearExternalIdNode = SubElement(yearDimensionNode, 'ExternalId')
				yearExternalIdNode.text = 'Year'
				yearLabelNode = SubElement(yearDimensionNode, 'Label')
				yearLabelNode.text = 'Year'
				yearTagsNode = SubElement(yearDimensionNode, 'Tags')
				yearTagsTagNode = SubElement(yearTagsNode, 'Tag')
				yearTagsTagLabelNode = SubElement(yearTagsTagNode, 'Label')
				yearTagsTagLabelNode.text = review['VehicleYear']

				makeDimensionNode = SubElement(tagsNode, 'TagDimension')
				makeDimensionNode.set('id', 'Make')
				makeExternalIdNode = SubElement(makeDimensionNode, 'ExternalId')
				makeExternalIdNode.text = 'Make'
				makeLabelNode = SubElement(makeDimensionNode, 'Label')
				makeLabelNode.text = 'Make'
				makeTagsNode = SubElement(makeDimensionNode, 'Tags')
				makeTagsTagNode = SubElement(makeTagsNode, 'Tag')
				makeTagsTagLabelNode = SubElement(makeTagsTagNode, 'Label')
				makeTagsTagLabelNode.text = review['VehicleMake']

			badgesNode = SubElement(rNode, 'Badges')
			badgeNode = SubElement(badgesNode, 'Badge')
			badgeNameNode = SubElement(badgeNode, 'Name')
			badgeNameNode.text = 'ContentImportSourceTireRack'
			badgeContentTypeNode = SubElement(badgeNode, 'ContentType')
			badgeContentTypeNode.text = 'REVIEW'
			badgeTypeNode = SubElement(badgeNode, 'BadgeType')
			badgeTypeNode.text = 'ContextDataValueBadge'


			CDVsNode = SubElement(rNode, 'ContextDataValues')
			cdvNode = SubElement(CDVsNode, 'ContextDataValue')
			cdvNode.set('id', 'TireRack')
			importSourceExternalIdNode = SubElement(cdvNode, 'ExternalId')
			importSourceExternalIdNode.text = 'TireRack'
			importSourceLabelNode = SubElement(cdvNode, 'Label')
			importSourceLabelNode.text = 'TireRack'
			
			cdvDimNode = SubElement(cdvNode, 'ContextDataDimension')
			cdvDimNode.set('id', 'ContentImportSource')	
			cdvDimExternalId = SubElement(cdvDimNode, 'ExternalId')
			cdvDimExternalId.text = 'ContentImportSource'
			cdvDimLabel = SubElement(cdvDimNode, 'Label')
			cdvDimLabel.text = 'ContentImportSource'

			
			userProfileNode = SubElement(rNode, 'UserProfileReference')
			
			if review['ReviewerId']: 
				profileExternalIDNode = SubElement(userProfileNode, 'ExternalId')
				profileExternalIDNode.text = review['ReviewerId']

			if review['ReviewerName']:
				profileNickNameNode = SubElement(userProfileNode, 'DisplayName')
				profileNickNameNode.text = review['ReviewerName']

			profileAnonymousNode = SubElement(userProfileNode, 'Anonymous')
			if review['ReviewerName']: 
				profileAnonymousNode.text = "false"
			else: 
				profileAnonymousNode.text = "true"

			profileHyperlinkingNode = SubElement(userProfileNode, 'HyperlinkingEnabled')
			profileHyperlinkingNode.text = "false"
		
			#submissionTime
			submissionNode = SubElement(rNode, 'SubmissionTime')
			submissionNode.text = time.strftime("%Y-%m-%dT%H:%M:%S", (time.strptime(review['SubmissionDate'], "%m/%d/%y")))

	clientProductFeed.write(xmlPrefix)
	clientProductFeed.write(tostring(root))

###################################################################
# Handle command line args
###################################################################

def main(argv):
	usage = 'usage: %prog [options] arg'
	parser = OptionParser(usage)
	parser.add_option('-c', '--clientName', help='Database name for the client', action='store', dest='clientName')
	parser.add_option('-i', '--input', help='Location of the CSV input file', action='store', dest='input')
	parser.add_option('-o', '--output', help='Location of the XML output file', action='store', dest='output')
	parser.add_option('-s', '--schema', default='6.9', help='The Bazaarvoice XML schema version', action='store', dest='schema')
	
	(options, args) = parser.parse_args()

	generateFeed(options)
	subprocess.call(['xmllint --schema http://www.bazaarvoice.com/xs/PRR/StandardClientFeed/' + options.schema + ' --noout ' + options.output], shell=True)


if __name__ == '__main__':
    main(sys.argv[1:])	





