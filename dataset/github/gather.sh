git log --branches --tags --remotes --full-history --date-order --format='%ai, %an, <%ae>, %h, %f, %P'

git issues -s closed > output-closed.csv
git issues -s open > output-open.csv
#
#sed 's/\s\+/,/g' output-closed.csv > tmp.csv
#rev tmp.csv | cut -c2- | rev | cut -c2- > output-closed.csv
#
#sed 's/\s\+/,/g' output-open.csv > tmp.csv
#rev tmp.csv | cut -c2- | rev | cut -c2- > output-open.csv
#rm tmp.csv
