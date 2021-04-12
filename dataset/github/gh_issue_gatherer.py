import argparse
import csv
import itertools
import os
import re
from subprocess import run, PIPE


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--repository', required=True,
                        help='Repository that should be examined')
    parser.add_argument('--limit', type=int, help='Limit number of issues')
    parser.add_argument('--state', help='State of the issues.',
                        choices=['open', 'closed', 'all'])
    return parser.parse_args()


def get_commentaries(author, comment):
    commentaries = {}
    resolution = 'Opened'
    if comment:
        # Get first author and map it to his commentary
        comment_author = re.match(r'author:\s(\w+)', comment)
        if comment_author:
            comment_author = comment_author.group(1)
        else:
            return commentaries, resolution
        start = re.search(r'status:\s\w+', comment).end()
        # Go trough author and status and strip them off the string
        for found_author, \
            found_status in zip(itertools.islice(re.finditer(r'author:\s(\w+)', comment), 1, None),
                                itertools.islice(re.finditer(r'status:\s\w+', comment), 1, None)):
            end = found_author.start()
            # todo: Comment should replace all occurrences of comma to semicolon
            if comment_author in commentaries:
                commentaries[comment_author].append(comment[start:end])
            else:
                commentaries[comment_author] = [comment[start:end]]
            # Change author and his start of the comment
            comment_author = found_author.group(1)
            start = found_status.end()
        # Append or add last commentary.
        if comment_author in commentaries:
            commentaries[comment_author].append(comment[start:])
        else:
            commentaries[comment_author] = [comment[start:]]
        if author in commentaries:
            resolution = 'In progress'
    return commentaries, resolution


def write_csv_file(repository, csv_output, header):
    # Insert header
    csv_output.insert(0, ['Issue id', 'Status', 'Summary', 'Issue Type',
                          'Created', 'Author', 'Resolution', 'Resolved',
                          'Description', 'Creator', 'Labels'] + header)
    # Change directory to root one
    os.chdir('../')
    with open(repository + '.csv', 'w') as file:
        writer = csv.writer(file, delimiter=',')
        writer.writerows(csv_output)


args = parse_args()
# Login to github using github CLI
run(['gh', 'auth', 'login'])
# The repository should be cloned inside this folder
os.chdir(args.repository)
limit = args.limit or 1000
state = args.state or 'open'
completed = run(['gh', 'issue', 'list', '--limit', str(limit), '-s', state],
                stdout=PIPE, stderr=PIPE)
stdout = completed.stdout.decode('utf-8')
remove_commas = stdout.replace(',', ';')
csv_convert = remove_commas.replace('\t', ',')
splitted = csv_convert.splitlines()
parsed_csv = list(csv.reader(splitted, delimiter=','))
header = []
# Maximum length of single entry in csv string
max_entry_length = 0
# Add description entries, resolved resolution, further labellings and
# commentaries to csv file
for entry in parsed_csv:
    # Set maximum numbers of authors of commentary
    max_commentary_authors = 6
    issue_number = entry[0]
    # Check issue description
    completed = run(['gh', 'issue', 'view', issue_number], stdout=PIPE,
                    stderr=PIPE)
    output = completed.stdout.decode('utf-8')
    # Commentary of issue to detect progress
    completed = run(['gh', 'issue', 'view', '-c', issue_number], stdout=PIPE)
    comment = completed.stdout.decode('utf-8')
    # Process description output
    lines = output.splitlines()
    try:
        author = lines[2][8:]
    except:
        continue
    # author
    entry.append(author)
    # Get commentaries
    commentaries, resolution = get_commentaries(author, comment)
    # Add resolution and resolved fields
    entry.append(resolution)
    entry.append('')
    if '<!--' in lines[9]:
        # remove commentary
        output = '\n'.join(lines[19:])
    else:
        output = '\n'.join(lines[9:])
    entry.append(output)
    # Creator and Labels
    entry.append('')
    entry.append('')
    # Comment when too many issues are inside repository
    for _, comments in zip(range(max_commentary_authors),
                           commentaries.items()):
        # Setup items from zipped for loop
        comment_author = comments[0]
        comments = comments[1]
        # Append new comment header and it's entries
        header.append('Comment author')
        entry.append(comment_author)
        header.append('Commentary')
        comment = ''.join(comments)
        entry.append(comment)
    if max_entry_length < len(entry):
        max_entry_length = len(entry)

for entry in parsed_csv:
    commentary_difference = max_entry_length - len(entry)
    for _ in range(commentary_difference):
        entry.append('')

# Write parsed csv to file
write_csv_file(args.repository, parsed_csv, header)
