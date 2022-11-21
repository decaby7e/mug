##  Filter gets executed

- Ensure that requirements are present
    - Database is reachable
    - Relevant CUPS folders can be read
- Read information from environment
    - sys.argv
    - stdin/filepath
    - CUPS environment variables
- Count number of pages
  - job_page_count >= quota : reject
  - else : pass on
