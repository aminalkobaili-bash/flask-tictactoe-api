# API examples (curl)

Base URL `http://127.0.0.1:5000`. Examples use `jq` to pull tokens and ids out of responses.
Board cells: `0` — empty, `1` — player 1 (X), `2` — player 2 / computer (O).

```bash
API=http://127.0.0.1:5000
```

## Auth

```bash
# Sign up two users
curl -s -X POST $API/signup -H 'Content-Type: application/json' -d '{"login":"alice","password":"alice-pass"}'
curl -s -X POST $API/signup -H 'Content-Type: application/json' -d '{"login":"bob","password":"bob-pass"}'
# -> 201 {"message": "User registered successfully"}; same login again -> 400

# Log in: returns {"type": "Bearer", "accessToken": ..., "refreshToken": ...}
LOGIN=$(curl -s -X POST $API/login -H 'Content-Type: application/json' -d '{"login":"alice","password":"alice-pass"}')
ACCESS=$(echo "$LOGIN" | jq -r .accessToken)
REFRESH=$(echo "$LOGIN" | jq -r .refreshToken)
BOB=$(curl -s -X POST $API/login -H 'Content-Type: application/json' -d '{"login":"bob","password":"bob-pass"}' | jq -r .accessToken)
# wrong password -> 401 {"error": "Invalid login or password"}

# New access token from a refresh token (refresh token stays the same)
curl -s -X POST $API/refresh/access -H 'Content-Type: application/json' -d "{\"refreshToken\":\"$REFRESH\"}"

# New access + refresh pair
curl -s -X POST $API/refresh/refresh -H 'Content-Type: application/json' -d "{\"refreshToken\":\"$REFRESH\"}"

# Token type is enforced: an access token here -> 401 "Invalid token type: expected refresh token"
curl -s -X POST $API/refresh/access -H 'Content-Type: application/json' -d "{\"refreshToken\":\"$ACCESS\"}"
```

## Users

```bash
curl -s $API/users/me -H "Authorization: Bearer $ACCESS"
# -> {"uuid": "...", "login": "alice"}
ALICE_ID=$(curl -s $API/users/me -H "Authorization: Bearer $ACCESS" | jq -r .uuid)

curl -s $API/users/$ALICE_ID -H "Authorization: Bearer $ACCESS"
curl -s $API/users/not-a-uuid -H "Authorization: Bearer $ACCESS"   # -> 400 Invalid UUID format

# No token -> 401 {"error": "Unauthorized", "message": "Bearer token required"}
curl -s $API/users/me
```

## Game vs computer

```bash
GAME=$(curl -s -X POST $API/games -H "Authorization: Bearer $ACCESS" \
  -H 'Content-Type: application/json' -d '{"game_type":"computer"}' | jq -r .uuid)

# A move = the whole board with exactly one new "1"; the computer answers in the same response
curl -s -X POST $API/game/$GAME -H "Authorization: Bearer $ACCESS" \
  -H 'Content-Type: application/json' -d '{"field":[[0,0,0],[0,1,0],[0,0,0]]}'

curl -s $API/games/$GAME -H "Authorization: Bearer $ACCESS"

# Validation errors -> 400
curl -s -X POST $API/game/$GAME -H "Authorization: Bearer $ACCESS" \
  -H 'Content-Type: application/json' -d '{"field":[[0,0,0],[0,0,0]]}'          # not 3x3
curl -s -X POST $API/game/$GAME -H "Authorization: Bearer $ACCESS" \
  -H 'Content-Type: application/json' -d '{"field":[[2,1,0],[0,1,0],[0,0,0]]}'  # changed opponent cell / several moves
```

## Game between two users

```bash
PVP=$(curl -s -X POST $API/games -H "Authorization: Bearer $ACCESS" \
  -H 'Content-Type: application/json' -d '{"game_type":"human"}' | jq -r .uuid)

curl -s $API/games -H "Authorization: Bearer $BOB"                 # games waiting for a second player
curl -s -X POST $API/games/$PVP/join -H "Authorization: Bearer $BOB"

curl -s -X POST $API/game/$PVP -H "Authorization: Bearer $ACCESS" \
  -H 'Content-Type: application/json' -d '{"field":[[1,0,0],[0,0,0],[0,0,0]]}'
curl -s -X POST $API/game/$PVP -H "Authorization: Bearer $ACCESS" \
  -H 'Content-Type: application/json' -d '{"field":[[1,1,0],[0,0,0],[0,0,0]]}'  # -> 400 "It's not your turn"
curl -s -X POST $API/game/$PVP -H "Authorization: Bearer $BOB" \
  -H 'Content-Type: application/json' -d '{"field":[[1,0,0],[0,2,0],[0,0,0]]}'
```

## History and leaderboard

```bash
curl -s $API/games/history -H "Authorization: Bearer $ACCESS"      # finished games of the current user
curl -s "$API/leaderboard?limit=3" -H "Authorization: Bearer $ACCESS"
# -> {"leaderboard": [{"uuid": "...", "login": "alice", "win_ratio": 1.5}, ...]}
curl -s "$API/leaderboard?limit=0" -H "Authorization: Bearer $ACCESS"  # -> 400
```

## Legacy endpoint (v1)

```bash
# Creates a game vs computer, kept from the first version of the API
curl -s -X POST $API/game -H "Authorization: Bearer $ACCESS"
```
