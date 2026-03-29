## RVAHelps.Me: The Privacy Shielded Community Navigator

Team: RVAHelpsMe

We built Rhonda, a low-latency navigator of local resources based on the communicated needs of the user that can summarize their issues for handoff to any agency, remember their progress to continue on another machine, while still never keeping any personal information. It's multilingual, accessible, empathetic, and completely anonymous.

## Pillar

Thriving and inclusive communities

## User

Richmond residents—especially immigrants, refugees, and those facing housing or financial instability—struggle to safely find and access existing support services. They constantly have to repeat the facts of their hardships over and over because there's no summary handoff between agencies and support services.

## Problem

In Richmond, the gap between life saving services and the people who need them is not a supply problem: it is a trust and accessibility problem. Current systems are fragmented, difficult to use, and require users to repeatedly explain their situation across agencies, creating friction that causes many to give up before receiving help.

Furthermore, when these residents finally do connect with the system, they are forced to repeat their traumatic stories to multiple case managers across different agencies because no secure, cross agency database exists.

We are decreasing the friction of accessing information about these resources and creating pathways to decrease having to repeatedly rehash traumatic life events.

## Why it matters

When access requires digital literacy, English proficiency, or sharing personal information, the most vulnerable residents are excluded. Improving safe discovery, navigation, and connection to services directly increases the number of people who successfully receive support.

## Alignment

This project aligns with both problems outlined in the thriving and inclusive communities pillar. RVAHelps.Me helps residents safely, and privately, discover and connect to trusted support services as well as helping residents navigate the right support services without needing to repeat their story.

## Rhonda

Rhonda listens to a user's description of their needs, in any language, replies to them with empathy and understanding. Using a human-verified repositority of local services, Rhonda can make the best suggestions for that user's issues.

Users can return to their progress with Rhonda using a simple anonymous passphrase.

Rhonda generates a "Progress Passport" in English and the user's language that can be displayed to social workers and other support staff to immediately know the user's situation and services connected with so far, speeding up intake, promoting cross-agency communication, and preventing the user from having to repeat traumatic details.

The application never stores any Personally Identifiable Information, not even analytics or tracking logs.

## Proposed solution

RVAHelps.Me is a privacy-first, multilingual, conversational interface that sits on top of existing systems like Help1RVA—without replacing them.

- No login, no PII, no tracking (privacy-first by design)
- Conversational navigation (Rhonda) replaces forms and search
- Multilingual + voice-friendly to reduce literacy and language barriers
- Anonymous Passport translates needs into structured signals (e.g., eviction risk, required documents), so residents don’t have to repeat their story
- Shareable outputs (SMS, WhatsApp, images) enable trusted community intermediaries to distribute information

This functions as a “front door” to services that reduces friction while strengthening—not replacing—existing human relationships

## Core user flow

**Step 1: The Multilingual Front Door and Transparent Privacy**

Before a user can interact with Rhonda, they are met with a plain language, highly visible privacy statement in English and other languages. Trust is established before the first interaction.

**Step 2: The 3-Word Passphrase**

Users do not create accounts, enter emails, or set passwords. Instead, Rhonda assigns them a random, 3-word passphrase like "APPLE BIRD RIVER". This phrase acts as an anonymous bookmark. It does not store a search history or a log of past messages: it simply stores the current state of the user's progress and needs. If a browser closes or a phone dies, typing these three words allows the user to resume their journey without starting over.

**Step 3: Conversational Search via Text and Voice**

Rhonda asks conversational, empathetic questions rather than requiring intake forms. If an older adult user clicks the "Hold to Speak" button and describes a need, Rhonda understands the intent via native audio processing. To protect privacy, Rhonda never requests GPS location.

**Step 4: The Anonymous Passport**

The anonymous passport is a secure, collaborative workspace shared by the resident with a service provider. It is the technical bridge that allows a resident to move between agencies without re-explaining their trauma.

Most "re-explaining" happens because intake workers start from zero with every client. The Passport stops this by shifting the conversation from Emotional Narrative to Administrative Status.

- **Translating Story to Intent**: Rhonda does not store the user's story. If a resident describes a traumatic eviction, Rhonda extracts the intent (e.g., status: imminent_eviction). When the worker scans the Passport, they do not ask "Tell me what happened," they say "I see you have an eviction notice, let's look at available funds".
- **Pre-Cleared Requirements**: The Passport lists what the resident has already gathered (e.g., utility_bill: true, photo_id: false). The worker instantly knows which internal forms to use without asking the resident why they lack specific documents.
- **Closing the Referral Loop**: If a resident was ineligible for a grant at one agency, that status is updated in the Passport. The next worker sees this immediately and avoids sending the resident back down a failed path.

## Data or document sources

[](https://github.com/hack4rva/pillar-thriving-inclusive-communities/blob/main/99_templates/project_one_pager_template.md#data-or-document-sources)

- Source 1
- Source 2
- Source 3

## MVP scope

By demo day, RVAHelps.Me will demonstrate a fully functional end-to-end experience focused on one to two high-impact use cases (e.g., rent assistance and food access):

- A working Progressive Web App interface accessible on mobile and desktop
- A conversational chat experience (Rhonda) that:
  - Understands user intent (e.g., “I need help paying rent”)
  - Asks clarifying, human-centered questions
  - Returns relevant local resources in plain language
- Generation of a 3 word anonymous passphrase to resume sessions
- A functional Anonymous Passport view, showing:
  - Interpreted needs (e.g., imminent eviction, food insecurity)
  - Pre-identified eligibility signals
  - Required documents checklist
- Ability to generate shareable outputs (text or simplified summaries) that can be sent via SMS or messaging apps
- Demonstration of privacy-first architecture (no login, no PII collection, no tracking)

## What this project does not do

Privacy for the end user is paramount for RVAHelps.Me 

It does NOT

- Require a login to access service information

- Store cookies on personal browsing history

- Collect name, address, zip code, phone number, email, immigration status, household number, or income

Rhonda assists Richmond residents in need and their trusted ambassadors to get them the help they need in whatever format is best received.  She is not a replacement for those who have created relationships with communities in Richmond.  She is there to support.  

******

## Risks and limitations

While RVAHelps.Me addresses critical gaps in access and trust, there are important limitations and risks:

- Service availability, eligibility, and hours frequently change. Without real-time integrations or provider partnerships, there is a risk of outdated information.
- Even with strong privacy design, users, especially undocumented or historically marginalized populations, may still be hesitant to engage with a digital tool.
- Rhonda is designed to support, not replace, case managers and community organizations. Over-reliance on the tool without human follow-up could limit effectiveness.
- Highly complex situations (e.g., overlapping legal, medical, and housing crises) may exceed what an MVP conversational system can safely guide.
- Language for digital co-pilot is not a human translation.in real-time. This
- While the Anonymous Passport concept does not need to be integrated into service systems, it would require providers to have some familiarity with its function.

## Demo plan

Our live demo will walk judges through a realistic user journey:

1. Opening the app
   - Show the multilingual, plain-language privacy statement
   - Emphasize no login, no tracking, no personal data collection
2. User interaction with Rhonda
   - Enter or speak a natural request (e.g., “I’m about to lose my apartment”)
   - Demonstrate conversational follow-up questions
   - Highlight how Rhonda interprets intent without requiring forms
3. Resource matching
   - Show curated, plain-language results from real Richmond services
4. Anonymous passphrase generation
   - Demonstrate how a user can leave and return without creating an account
5. Anonymous Passport
   - Show how the system translates narrative into structured needs
   - Display document checklist and status indicators
   - Explain how this reduces repeated storytelling
6. Shareable output
   - Generate a simple message or summary that could be sent via SMS or WhatsApp
   - Highlight use by community ambassadors or case managers

We will close by reinforcing how this experience reduces friction, preserves dignity, and increases successful connections to services.

## Longer-term potential

We foresee this project to be a great navigation tool to pair with Help1RVA.
