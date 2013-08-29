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
	'TractionRating',
	'DurabilityRating', 
	'ComfortRating', 
	'ReviewerName', 
	'ReviewerId',
	'ReviewTitle',
	'ReviewSummary',
	'IPAddress',
	'TireMake',
	'TireModel',
	'VehicleYear',
	'VechicleModel',
	'ProductId'
]

def populateTags(parentTag, tagTitle, tagText):
	node = SubElement(parentTag, tagTitle)
	node.text = tagText

def CheckForExistence(line, num, lineNum, errorFile):
	result = True

	try: 
		line[num].encode('UTF-8', 'strict')
	except UnicodeDecodeError:
		errorFile.write("line" + str(lineNum) + "\tcolumn: " + str(num) + "\t" + str(line) + "\n")
		result = False
	except IndexError:
		errorFile.write("line" + str(lineNum) + "\tcolumn: " + str(num) + "\t" + str(line) + "\n")
		result = False	
	return result

def parseLine(line, reviewDict, errorFile):

	validColumns = True

	for column in column_map:
		try: 
			reviewDict[column] = re.sub('\n\t', ' ', line[column_map.index(column)].encode('utf-8'))
		except UnicodeDecodeError:
			errorFile.write(str(line) + '\n')
			validColumns = False
	
	if not validColumns: 
		reviewDict = {}

	return reviewDict

def roundRating(rawRating):

	decimalValue = math.modf(rawRating)[0]

	if decimalValue >= .5:
		roundedRating = math.ceil(rawRating)
	else:
		roundedRating = math.floor(rawRating)

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
	#reader.next() 

	for line in reader:
		_review = {}
		_review = parseLine(line, _review, errorFile)

		if not _review.keys():
			continue
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
				ratingNode.text = roundRating(float(review['OverallRating']))

			ratingsOnlyNode = SubElement(rNode, 'RatingsOnly')

			if review['ReviewSummary'] or review['ReviewSummary']:
				ratingsOnlyNode.text = 'false'
			else:
				ratingsOnlyNode.text = 'true'

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
	#subprocess.call(['xmllint --schema http://www.bazaarvoice.com/xs/PRR/StandardClientFeed/' + options.schema + ' --noout ' + options.output], shell=True)


if __name__ == '__main__':
    main(sys.argv[1:])	





