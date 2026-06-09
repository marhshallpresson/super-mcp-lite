#!/bin/bash
for d in ~/Projects/*/; do
    echo "Processing $d..."
    cd "$d" || continue
    if [ -d .git ]; then
        # Check current remote url
        url=$(git remote get-url origin 2>/dev/null)
        
        # Convert HTTPS to SSH if necessary
        if [[ $url == https://github.com/* ]]; then
            echo "Converting HTTPS remote to SSH for $d"
            new_url=${url/https:\/\/github.com\//git@github.com:}
            git remote set-url origin "$new_url"
        fi
        
        echo "Fetching git activity for $d..."
        git fetch --all
    else
        echo "No .git folder found in $d"
    fi
done
echo "Git synchronization complete!"
