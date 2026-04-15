---
on:
  pull_request:
    types: [closed]
    branches: [main]
permissions:
  contents: read
  pull-requests: read
safe-outputs:
  jobs:
    bump-version-and-release:
      description: "Bump version in pyproject.toml based on PR labels and create a GitHub release"
      runs-on: ubuntu-latest
      output: "Version bumped and release created!"
      permissions:
        contents: write
      steps:
        - name: Checkout
          uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683  # v4
          with:
            fetch-depth: 0
            ref: main

        - name: Check if PR was merged
          id: check
          run: |
            if [ -f "$GH_AW_AGENT_OUTPUT" ]; then
              BUMP_TYPE=$(cat "$GH_AW_AGENT_OUTPUT" | jq -r '.items[] | select(.type == "bump_version_and_release") | .bump_type // "patch"')
              RELEASE_TITLE=$(cat "$GH_AW_AGENT_OUTPUT" | jq -r '.items[] | select(.type == "bump_version_and_release") | .release_title // ""')
              RELEASE_NOTES=$(cat "$GH_AW_AGENT_OUTPUT" | jq -r '.items[] | select(.type == "bump_version_and_release") | .release_notes // ""')
            else
              BUMP_TYPE="patch"
              RELEASE_TITLE=""
              RELEASE_NOTES=""
            fi
            echo "bump_type=$BUMP_TYPE" >> $GITHUB_OUTPUT
            echo "release_title=$RELEASE_TITLE" >> $GITHUB_OUTPUT

            # Save release notes to file to handle multiline
            echo "$RELEASE_NOTES" > /tmp/release_notes.md

        - name: Set up Python
          uses: actions/setup-python@42375524e23c412d93fb67b49958b491fce71c38  # v5
          with:
            python-version: '3.12'

        - name: Bump version
          id: bump
          env:
            BUMP_TYPE_INPUT: ${{ steps.check.outputs.bump_type }}
          run: |
            BUMP_TYPE="$BUMP_TYPE_INPUT"
            CURRENT=$(grep -oP 'version = "\K[^"]+' pyproject.toml)
            IFS='.' read -r MAJOR MINOR PATCH <<< "$CURRENT"

            case "$BUMP_TYPE" in
              major)
                MAJOR=$((MAJOR + 1))
                MINOR=0
                PATCH=0
                ;;
              minor)
                MINOR=$((MINOR + 1))
                PATCH=0
                ;;
              patch|*)
                PATCH=$((PATCH + 1))
                ;;
            esac

            NEW_VERSION="$MAJOR.$MINOR.$PATCH"
            echo "current=$CURRENT" >> $GITHUB_OUTPUT
            echo "new_version=$NEW_VERSION" >> $GITHUB_OUTPUT
            echo "Bumping $CURRENT -> $NEW_VERSION ($BUMP_TYPE)"

            # Update pyproject.toml
            sed -i "s/version = \"$CURRENT\"/version = \"$NEW_VERSION\"/" pyproject.toml

        - name: Update CHANGELOG
          env:
            NEW_VERSION: ${{ steps.bump.outputs.new_version }}
          run: |
            DATE=$(date -u +%Y-%m-%d)
            RELEASE_NOTES=$(cat /tmp/release_notes.md)

            # Prepend new version entry after the header
            sed -i "/^## \[/i ## [$NEW_VERSION] - $DATE\n\n$RELEASE_NOTES\n" CHANGELOG.md

        - name: Commit and tag
          env:
            NEW_VERSION: ${{ steps.bump.outputs.new_version }}
          run: |
            git config user.name "github-actions[bot]"
            git config user.email "github-actions[bot]@users.noreply.github.com"
            git add pyproject.toml CHANGELOG.md
            git commit -m "chore: bump version to $NEW_VERSION" || echo "No changes to commit"
            git tag "v$NEW_VERSION"
            git push origin main --tags

        - name: Create GitHub Release
          env:
            GH_TOKEN: ${{ github.token }}
            NEW_VERSION: ${{ steps.bump.outputs.new_version }}
            RELEASE_TITLE_INPUT: ${{ steps.check.outputs.release_title }}
          run: |
            RELEASE_TITLE="$RELEASE_TITLE_INPUT"
            if [ -z "$RELEASE_TITLE" ]; then
              RELEASE_TITLE="v$NEW_VERSION"
            fi
            gh release create "v$NEW_VERSION" \
              --target main \
              --title "$RELEASE_TITLE" \
              --notes-file /tmp/release_notes.md
---

# Auto Version Bump and Release

When a pull request is merged to main, analyze the PR to determine the version bump type and generate release notes.

## Instructions

1. Read the merged pull request title, body, labels, and changed files
2. Determine the version bump type based on these rules:
   - **major**: PR has label `breaking-change` or title contains "BREAKING"
   - **minor**: PR has label `feature` or `enhancement`, or title starts with `feat:`
   - **patch**: All other cases (bug fixes, refactoring, docs, chores)
3. Generate concise release notes in Chinese (zh-CN) summarizing the changes, formatted as markdown with sections like `### 新增`, `### 修复`, `### 改进`, `### 变更`
4. Generate a release title in format `v{version} — {brief_description}`
5. Only proceed if the PR was actually merged (not just closed)

## Output

Use the `bump-version-and-release` tool with:
- `bump_type`: "major", "minor", or "patch"
- `release_title`: The release title
- `release_notes`: The release notes in markdown format
