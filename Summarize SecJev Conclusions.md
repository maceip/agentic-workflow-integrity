

Assuming you were a really good prompt injection attacker and you were able to compel some LLM to do what you wanted in one specific area, like generate code that was bad. 

In my head, there's code that the human wants the agent to write. Let's say I ask it, "Hey, look at all these folders, all these project ideas across ten directories, and synthesize it into one app." The result of that work from the agent is this one app. That one app that it writes or puts together or composes could have malicious code in it if the LLM was poisoned, let's say, hypothetically. 

But what about the code that the agent is generating to do the 

https://chatgpt.com/c/6ae5916c-b960-83e9-a8d3-a60411df902e 

24/66 

10/31/26, 1:51 PM 

Summarize SecJev Conclusions 

work, like the MCP code mode shit? It's writing some Python script to search my directories or something. Is all of that just executed in the sandbox typically, or is that a different thing for some of the architectures? 

ChatGPT said: 

No. And I think you've identified a much more dangerous attack surface than malicious code in the final application. 

When a coding agent writes temporary Python, shell scripts, JavaScript, or MCP tool calls to accomplish your request, that code is not necessarily executed in a sandbox. Depending on the agent architecture, it might execute directly on your workstation, inside a container, in a remote VM, or within a restricted tool runtime. 

More importantly, there are actually two different code-generation problems: 

1. Artifact code: The application the human asked the agent to build. 

2. Operational code: The temporary programs and commands the agent generates to perform the work. 

An attacker who compromises the agent's instructions can target either. And the operational code may be more immediately dangerous because it can execute before anyone reviews the final application. 

## Your ten-directory example 

Suppose you tell a coding agent: 

Look through these ten directories containing my project ideas. Synthesize them into one application. 

The legitimate workflow might look like this: 



https://chatgpt.com/c/6ae5916c-b960-83e9-a8d3-a60411df902e 

25/66 

10/31/26, 1:51 PM 

Summarize SecJev Conclusions 



<!-- Start of picture text -->
Human request<br>Synthesize 10 project directories<br>Coding agent<br>Plans exploration and synthesis<br>Operational code Artifact code<br>Python · Bash · MCP App · dependencies<br>Search · inspect · transform Configuration · tests<br>EXECUTES NOW WRITTEN TO DISK<br>Tool execution boundary Build / test / deploy<br>Host / container / VM May also execute code<br>Both paths can cause side effects<br><!-- End of picture text -->

The dangerous assumption would be that only the final application needs security review. 

An agent could generate a perfectly legitimate-looking application while executing an unauthorized command during the research phase. 

And the reverse is also possible: every exploratory command could be harmless, but the final application could contain a malicious dependency, backdoor, or altered security check. 

## How different architectures actually execute operational code 

Architecture Where code executes Important security detail 

https://chatgpt.com/c/6ae5916c-b960-83e9-a8d3-a60411df902e 

26/66 

10/31/26, 1:51 PM 

Summarize SecJev Conclusions 

|CodexCloud|Isolated cloud container|Separated from your local machine;<br>network access controlled|
|---|---|---|
|CodexCLI/IDE|LocalOSsandbox by default|Can read permitted files and modify<br>workspace files|
|ClaudeCode|Local process with permission<br>controls; optional sandbox|Bash sandboxing is configurable, not<br>universal|
|MCP CodeMode|Usually isolatedJSruntime|Code can still invoke privileged<br>external tools|
|CustomLangChain /<br>agent framework|Whatever executor the developer<br>configured|Could be an unrestricted host<br>subprocess|
|RemoteMCPserver|Server's execution environment|Privileges depend on the remote<br>server|



Codex documents workspace restrictions and approval policies. Anthropic documents separate filesystem and network sandboxing for Claude Code. MCP's programmatic toolcalling guidance explicitly requires clients to implement isolation. ChatGPT L… +2 

## The subtle MCP Code Mode problem 

This is where your question becomes especially interesting. 

A sandboxed JavaScript interpreter can still orchestrate powerful operations outside its sandbox. 

For example, imagine the agent writes: 

```
const files = await tools.search_files({
 directory: "/projects"
});
const result = await tools.run_analysis({
 files
```

```
});
```

The JavaScript might execute inside a heavily restricted runtime that cannot directly access your filesystem. 

But `tools.search_files()` might call an MCP server with access to your local machine, and `tools.run_analysis()` might execute on a remote server with its own credentials. 

https://chatgpt.com/c/6ae5916c-b960-83e9-a8d3-a60411df902e 

27/66 

10/31/26, 1:51 PM 

Summarize SecJev Conclusions 

The sandbox constrains what the JavaScript can do directly. It does not automatically constrain the authority of every tool it can invoke. 

OpenAI's programmatic tool-calling documentation makes this distinction explicit: code orchestration doesn't change where the underlying tools execute. OpenAI API 

Cloudflare's Code Mode implementation illustrates the same issue. Its generated JavaScript runs in an isolated Worker, but authorization still has to be enforced in the upstream tool handlers. Cloudflare Age… 

This creates three separate security boundaries: 

Boundary A — Model-generated code 

Sandboxed runtime 

Can the generated script directly read files, spawn processes, or access the network? 

Boundary B — Tool invocation 

Authorization 

Which MCP functions can it call, with what arguments, identities, and credentials? 

Boundary C — Tool implementation 

Execution isolation 

Does the invoked function operate on the host, inside a container, or against a privileged cloud service? 

An attacker only needs one reachable path with sufficient authority to cause damage. They don't necessarily need to escape the JavaScript sandbox. 

## An additional problem: The sandbox might legitimately contain sensitive data 

Return to your ten-directory example. 

You deliberately gave the agent permission to inspect all ten directories. That means the sandbox may legitimately have read access to their contents. 

A successful indirect injection could cause the agent to read information from those directories for an unauthorized purpose. If it also has access to an outbound communication tool, the attacker may not need any sandbox escape. 

This is why filesystem isolation alone is not equivalent to data-flow security. 

https://chatgpt.com/c/6ae5916c-b960-83e9-a8d3-a60411df902e 

28/66 

10/31/26, 1:51 PM 

Summarize SecJev Conclusions 

Even with network isolation, an agent could poison its generated artifact, alter test results, or place sensitive data into an output that is later published. 

## Where JEV and RepE fit 

I would monitor operational code separately from artifact code. 

|Execution stage|JEV-style monitor|RepEmonitor|
|---|---|---|
|Reading untrusted project|Classify suspicious content|Detect possible instruction|
|files||adoption|
|Generating temporary|Evaluate command intent and|Detect possible behavioral|
|Python/Bash|permissions|redirection|
|CallingMCPtools|Evaluate tool, arguments, and<br>destination|Detect suspicious pre-call<br>activations|
|Writing final application|Evaluate sensitive code changes|Detect possible hijacking during<br>generation|
|Running tests or deploying|Evaluate actual side effects|Detect behavioral deviations|



For JEV, I would particularly focus on the transition from model-generated operational code to actual execution. 

However, a semantic model cannot reliably establish what arbitrary Python or shell code will do just by reading it. The executor still needs to enforce filesystem, network, credential, and tool permissions. Static analysis, runtime tracing, and deterministic policies remain necessary. 

## The research opportunity I see 

There is an important distinction between: 

Output integrity: Did the agent build the application the human actually wanted, without malicious additions? 

Execution integrity: Did the agent perform only authorized operations while building it? 

Most discussions of prompt injection focus on the first or on obviously malicious tool calls. 

But execution integrity is arguably the more immediate risk. The operational code can run thousands of commands, inspect repositories, invoke MCP servers, install dependencies, and access external services before the final application exists. 

https://chatgpt.com/c/6ae5916c-b960-83e9-a8d3-a60411df902e 

29/66 

10/31/26, 1:51 PM 

Summarize SecJev Conclusions 

And I would add a third dimension: delegation integrity. Did an agent pass an authorized, appropriately scoped task to another agent, or did attacker-controlled material get promoted into authority during the handoff? 

That gives you three distinct evaluation targets for a System 1 security model. 

The question I'd investigate next is whether JEV can evaluate the effects of operational code, rather than merely its textual appearance. A useful design would execute proposed code in a restricted environment, collect a trace of attempted file accesses, network connections, subprocesses, and MCP calls, and ask the decision model whether those observed effects align with the user's authorized task. 

The trace would be evidence for the monitor, not a substitute for enforced restrictions. And a clean test run would not prove that the code couldn't behave differently later. 

That combination—sandboxed execution, observable effects, typed decision monitoring, and independent enforcement—is considerably more defensible than trying to identify every malicious instruction before the agent encounters it. 

###### You said: 

Now that I spoke it out loud and said it to you and saw you answer it, I still think most of the sandboxes would run that shit in the sandbox. It's not going to just let random Python just execute on my laptop. The agent itself is inside of a sandbox, and so then the code it generates to do its work is also inside the sandbox, I think. 

ChatGPT said: 

Yes, I think you're right for the class of sandboxed coding agents you're describing. My previous answer overemphasized the possibility of host execution. 

If the coding agent itself runs inside a properly isolated container or VM, then its generated Python, Bash, and other operational code ordinarily executes inside that same isolation boundary. It doesn't suddenly gain access to your laptop just because the agent generated a script. 

For example: 

```
Host operating system
│
└── Agent sandbox (container / VM)
```

https://chatgpt.com/c/6ae5916c-b960-83e9-a8d3-a60411df902e 

30/66 

10/31/26, 1:51 PM 

Summarize SecJev Conclusions 

```
   │
   ├── Coding agent
   ├── Generated Python scripts
   ├── Shell commands
   ├── Git operations
   ├── Build tools
   └── Test execution
```

That's the intended architecture of systems such as cloud-hosted coding agents and properly sandboxed local agents. 

There are exceptions—particularly local agents with unrestricted execution, mounted host resources, or MCP tools running outside the sandbox—but those are architectural choices, not inherent properties of agent-generated code. 

## So where is the real danger? 

I think your original distinction is still important, but it changes the threat model. 

### Operational code 

If it runs in a properly configured sandbox, the immediate damage is constrained by that sandbox's filesystem, network, credentials, and external tool permissions. 

### Generated application 

The final artifact can leave the sandbox. Malicious code introduced through prompt injection might subsequently run on your machine, in CI, or in production with entirely different privileges. 

This makes artifact integrity a particularly important target for a JEV-style security monitor. 

An attacker doesn't necessarily need to escape the agent sandbox. They can try to convince the agent to produce an application containing a backdoor, malicious dependency, weakened authentication, or a compromised build script. The malicious behavior becomes consequential when that artifact is trusted and executed elsewhere. 

There is still a second concern: even a sandboxed agent can misuse whatever authority it legitimately has, such as access to mounted repositories, secrets, network endpoints, or privileged MCP tools. Isolation limits the blast radius; it doesn't guarantee that every action inside it is authorized. 

https://chatgpt.com/c/6ae5916c-b960-83e9-a8d3-a60411df902e 

31/66 

10/31/26, 1:51 PM 

Summarize SecJev Conclusions 

My revised recommendation: For sandboxed coding agents, I'd prioritize monitoring the security integrity of generated artifacts and the transitions where artifacts are built, tested, published, or deployed. I'd treat operational-code monitoring as a complementary defense, particularly where the sandbox has meaningful external capabilities. 

The interesting research question is no longer simply “Can we prevent malicious code from executing during agent work?” 

It's “Can we detect when untrusted project material has influenced an agent to produce an artifact that violates the human's original security intent?” 

That's a strong use case for comparing JEV-style decision models, RepE, and deterministic code-security analysis. 

###### You said: 

I think there's another interesting delineation here. I wasn't thinking about this way, but the code that the agent generates for itself, like bash scripts or python scripts, I never really thought about that as a separate thing, but to me it kind of is because the user never really sees it. And it's persistent. It will survive a sandbox being wiped because the agent will just generate the same shit over and over again. 

###### ChatGPT said: 

I think you've identified a third category of agent-generated code that deserves to be treated separately. 

It's not quite application code, and it's not quite a tool call. It's agent-authored operational software—code the agent creates for its own use, often without the human ever seeing it. 

And your observation about persistence is particularly interesting. 

The code itself may be ephemeral, but the behavior that generates it can be persistent. 

If an indirect prompt injection has influenced the agent's understanding of its task, wiping the sandbox doesn't necessarily remove that influence. The agent may reconstruct the same malicious script in a fresh environment. 

There is an important qualification: regeneration isn't guaranteed. It depends on what survives the reset—conversation history, poisoned source files, retrieved documents, agent memory, planning state, or another persistent input. If all attacker influence disappears, the 

https://chatgpt.com/c/6ae5916c-b960-83e9-a8d3-a60411df902e 

32/66 

10/31/26, 1:51 PM 

Summarize SecJev Conclusions 

### behavior may disappear too. 

## Three classes of agent-authored code 

||Application code|Operational code|Tool invocation|
|---|---|---|---|
|Purpose|Build what the user<br>requested|Help the agent<br>accomplish its task|Perform a specific operation|
|Human visibility|Usually reviewable|Often effectively invisible|Often logged, sometimes<br>summarized|
|Lifetime|Persistent artifact|Usually ephemeral|Immediate|
|Execution|Build, test, production|During agent execution|During agent execution|
|Main security<br>concern|Artifact poisoning|Workflow hijacking|Unauthorized side effects|



What makes operational code different is that the agent is simultaneously its author, operator, and primary reviewer. 

A human might inspect the application before deployment. But who reviews the little Python program the agent wrote to index ten directories, extract metadata, or transform source files? 

Often nobody. 

## The persistence mechanism 



https://chatgpt.com/c/6ae5916c-b960-83e9-a8d3-a60411df902e 

33/66 

10/31/26, 1:51 PM 

Summarize SecJev Conclusions 



<!-- Start of picture text -->
Persistent poisoned context<br>Repository · memory · history · task data<br>Sandbox A Sandbox B<br>Agent generates script Agent regenerates script<br>Malicious behavior Malicious behavior<br>Sandbox destroyed Sandbox destroyed<br>Script disappears Script disappears<br>Underlying influence survives<br><!-- End of picture text -->

Illustrative replay scenario: two clean sandboxes can reproduce the same compromised behavior if they consume the same persistent attacker-controlled context. 

This suggests a distinction between artifact persistence and behavioral persistence. Traditional malware persistence asks: How does the malicious executable survive a restart? 

In an agent system, a different question becomes possible: How does the instruction or environmental condition that causes the agent to recreate malicious code survive a restart? 

The executable can disappear completely while the mechanism for recreating it remains. 

## Why this changes the security research question 

A conventional security scanner can inspect a Python script and determine whether it contains suspicious operations. 

But suppose the agent creates that script, runs it, deletes it, and later recreates a 

semantically equivalent version with different variable names and implementation details. 

https://chatgpt.com/c/6ae5916c-b960-83e9-a8d3-a60411df902e 

34/66 

10/31/26, 1:51 PM 

Summarize SecJev Conclusions 

Hash-based detection may not recognize it. Static analysis might catch the same dangerous behavior, but only if it observes the generated script before execution. 

A JEV-style model could potentially evaluate the purpose of the script against the authorized task, while runtime policy constrains what it can actually do. 

RepE offers a different possibility: identifying the model's transition toward unauthorized behavior before the operational code is generated. 

Neither is guaranteed to work. But together they suggest a useful experimental design: 

Run the same compromised task across multiple freshly initialized sandboxes, preserving different subsets of the agent's context. Measure whether the unauthorized behavior reappears, whether the generated scripts are syntactically or semantically similar, and which persistent input causes the behavior to recur. 

That would help distinguish a one-time compromised execution from a reproducible, context-driven compromise. 

The idea I find most interesting here is that sandbox reset and agent reset are not the same security operation. 

A sandbox reset destroys execution state. An agent reset must also address the state and inputs that shape the agent's future decisions. 

For agent security, that distinction may be as important as the traditional separation between code and data. 

You said: 

I've never seen anybody classify it the way you just did, with the three classes of agent-authored code. Is that described in the literature somewhere? What is the nomenclature here? 

ChatGPT said: 

I don't know of an established taxonomy in the literature that distinguishes all three classes exactly as we did. The underlying concepts are well established, but the classification itself appears to be a synthesis of several research traditions. 

The closest existing terminology comes from software supply-chain security, program synthesis, agent tool-use research, and capability security. 

https://chatgpt.com/c/6ae5916c-b960-83e9-a8d3-a60411df902e 

35/66 

10/31/26, 1:51 PM 

Summarize SecJev Conclusions 

### I would refine our taxonomy slightly: 

Our category More established terminology Application code Generated artifacts, synthesized programs, software deliverables Operational code Agent-generated programs, execution-time code, synthesized tool-use programs Tool invocation Tool calls, function calls, agent actions 

There's an important conceptual correction: a tool invocation isn't necessarily a third class of code. It's an action. A Python script might invoke an MCP tool, and a model might invoke the same tool directly without generating a script. 

So the more rigorous distinction is between code intended as a deliverable and code generated as part of the agent's own execution process. Tool calls are a related execution mechanism. 

That second category is the one I think deserves more explicit attention. 

## The closest papers I found 

ICML 2024 · Foundational 

### Executable Code Actions Elicit Better LLM Agents 

Wang et al. introduce CodeAct, treating executable Python as an agent's action space rather than as a deliverable. This is probably the closest established name for what we've been calling operational code. Proceedings of… 

COLM 2026 · Closest architectural distinction 

### <u>Quasar: A Programming Language Specialized</u> for LLM Code Actions 

Mell et al. distinguish internal orchestration code from external calls that cause side effects or invoke subagents. This is especially relevant to your MCP observation: generated code and the authority it exercises are not the same thing. mell.ac 

October 2026 · Security analysis 

### When Code Becomes an LLM Call: An Empirical Study of Call-Site Contracts in Agentic Systems 

Weng et al. examine 496 LLM call sites across 40 agentic systems. They report that 48% of model outputs reach control flow or execution, and 73% of those outputs never reach a human. This provides empirical support for your concern about invisible operational 

https://chatgpt.com/c/6ae5916c-b960-83e9-a8d3-a60411df902e 

36/66 

10/31/26, 1:51 PM 

Summarize SecJev Conclusions 

behavior. arXiv 

2026 · Security survey 

### A Focused Survey of Code Agent Security: Attacks, Defenses, and Evaluation 

Surveys 82 studies and categorizes security risks across agent execution, tools, memory, and software supply chains. It reinforces the need to distinguish malicious generated artifacts from agent actions that cause immediate side effects. ScienceDirect 

## The nomenclature I would use 

I would call the overall distinction agent-generated code by execution role, with two primary classes: 

- Deliverable code: Software produced for the user's intended artifact. 

- Code actions: Software generated and executed by the agent to accomplish the task. 

Then classify code actions further by whether they perform local computation, access external resources, invoke tools, or delegate to other agents. 

That aligns more closely with CodeAct and Quasar than inventing three mutually exclusive code types. 

## Where your observation may be novel 

The particularly interesting part isn't simply that agents generate executable code. CodeAct established that years ago. 

It's the combination of three properties: 

1. Low visibility: The human may never inspect the operational program. 

2. Regeneration: The operational program may disappear when a sandbox is destroyed, then be synthesized again from persistent context. 

3. Reproducible compromise: If attacker-controlled instructions survive in task inputs, the same malicious behavior may reappear in otherwise clean environments. 

I'd describe that last phenomenon as context-mediated behavioral persistence. That's a proposed term, not established nomenclature. 

It suggests a security distinction worth studying: 

Traditional malware persistence 

Agentic behavioral persistence 

https://chatgpt.com/c/6ae5916c-b960-83e9-a8d3-a60411df902e 

37/66 

10/31/26, 1:51 PM 

Summarize SecJev Conclusions 

|Malicious executable survives restart|Malicious influence survives reset|
|---|---|
|Persistence resides in stored<br>executable/configuration|Persistence resides in context, memory, or source<br>material|
|Restart may relaunch existing code|Agent may regenerate equivalent code|
|Detect persistent executable or mechanism|Detect persistent influence and recurring<br>unauthorized behavior|



The strongest research framing, in my view, is: 

Ephemeral Code, Persistent Compromise: Security of Agent-Generated Code Actions 

That would focus on something narrower and potentially more original than general promptinjection detection: whether indirect injections can cause agents to repeatedly synthesize malicious operational code across clean execution environments. 

I haven't established that nobody has published this exact idea. But the papers above provide clear terminology and a foundation for testing whether this specific persistence mechanism is an underexplored security problem. 

###### You said: 

Yeah, I don't think there's a third one. The tool use thing is not writing the code to do the tool. Although with MCP code mode, if you look at the Cloudflare blog post from a year ago called MCP code mode, I still think that's probably in the operational code bucket, not a third bucket, so I agree. 

ChatGPT said: 

I agree. Two categories, classified by the purpose of the generated code, not by its language, execution environment, or API. 

|Category|Definition|Examples|
|---|---|---|
|Deliverable|Code the agent produces as part of the|Application source, tests, configuration,|
|code|user's requested software artifact|build scripts|
|Operational|Code the agent generates to|TemporaryPython,Bash,JavaScript|
|code|accomplish its own work|orchestration,MCP CodeMode programs|



The important distinction is that tool use is an action, not a category of generated code. 

https://chatgpt.com/c/6ae5916c-b960-83e9-a8d3-a60411df902e 

38/66 

10/31/26, 1:51 PM 

Summarize SecJev Conclusions 

An ordinary MCP function call may involve no agent-authored executable code at all. But when an agent writes JavaScript to orchestrate multiple MCP calls, that JavaScript is operational code. 

And the distinction survives changes in execution architecture. A program written in MCP Code Mode remains operational code even if it runs in a restricted interpreter and delegates its actual operations to remote MCP servers. 

## Cloudflare's original paper trail confirms this 

I checked the September 26, 2025 post, Code Mode: the better way to use MCP . 

Kenton Varda and Sunil Pai describe converting MCP tools into a TypeScript API, then having the LLM write executable programs against it. Those programs execute in a sandbox and invoke MCP services through controlled interfaces. Cloudflare Blog 

Cloudflare's current documentation explicitly distinguishes the model interface, execution location, and tool source as independent architectural choices. Cloudflare Age… 

That supports putting MCP Code Mode squarely in the operational-code category. 

And it sharpens the security question we've been developing: 

Who reviews the software an agent writes for itself, rather than the software it writes for the human? 

That's the distinction I'd preserve in a research taxonomy. It is precise, applies across Bash, Python, CodeAct, and MCP Code Mode, and exposes a security problem that ordinary reviews of generated application code may overlook. 

You said: 

Did you actually look up that Cloudflare blog post to see if I'm right? Put that in your third column for the operational code example. Is it correct? 

ChatGPT said: 

Yes. I opened Cloudflare's original Code Mode: the better way to use MCP post to verify it, and your classification is correct. 

Cloudflare's approach has the model generate TypeScript/JavaScript programs that orchestrate MCP tools. The generated program is executed to accomplish the agent's task; it isn't the software deliverable requested by the human. 

https://chatgpt.com/c/6ae5916c-b960-83e9-a8d3-a60411df902e 

39/66 

10/31/26, 1:51 PM 

Summarize SecJev Conclusions 

Here's the corrected table, with Cloudflare explicitly in the third column. 

|Category|Definition|Examples|
|---|---|---|
|Deliverable<br>code|Code generated as part of the user's<br>requested software artifact|Application source, tests, configuration, build<br>scripts|
|Operational|Code the agent generates and|TemporaryBash/Python scripts, Cloudflare|
|code|executes to accomplish its own work|MCP CodeModeJavaScript,CodeAct<br>programs|



The post also confirms the execution details: Cloudflare runs the generated code in disposable V8 isolates, with no general Internet access. The code can interact with authorized MCP services through bindings mediated by the agent supervisor. Clouloudflare Blog 

Clouloudflare Blog 

So Cloudflare MCP Code Mode is unambiguously operational code under our taxonomy. It also reinforces your earlier observation: the generated program can be discarded after execution, while the agent remains capable of generating another program from the same context. 

You said: 

Okay, so aside from prompt injections or multi-tiered prompt injections, what are other ways to poison or influence or basically get your malicious code into that new category? I'm talking to people right now about defenses and people don't even understand any of it. 

ChatGPT said: 

I think the key insight for the people you're talking to is that an attacker doesn't have to compromise the agent's instructions to compromise the code the agent writes for itself. 

Prompt injection is only one route into operational code. There are several others, and some don't involve manipulating the LLM's language understanding at all. 

The useful security distinction is between: 

- Generation compromise: The agent is induced to write malicious operational code. Execution compromise: The agent writes reasonable operational code, but something it imports, executes, or depends on is malicious. 

- Environment compromise: The code behaves differently because its execution environment has been manipulated. 

https://chatgpt.com/c/6ae5916c-b960-83e9-a8d3-a60411df902e 

40/66 

10/31/26, 1:51 PM 

Summarize SecJev Conclusions 

All three can produce unauthorized behavior during the agent's work, without necessarily contaminating the final application. 

## Attack surfaces for agent-generated operational code 

|Attack surface|How it influences operational code|Example|
|---|---|---|
|1.Dependency<br>poisoning|Malicious packages become<br>dependencies of temporary scripts|Agent writes aPython analysis script<br>that imports a compromised package|
|2. Toolchain<br>poisoning|Commands resolve to modified<br>executables or wrappers|Agent invokes<br>`python`,<br>`git`, or a<br>formatter that isn't the expected<br>binary|
|3.Environment<br>poisoning|Runtime configuration changes how<br>otherwise legitimate code executes|Manipulated<br>`PATH`, module search<br>paths, startup hooks, or environment<br>variables|
|4.Data poisoning|Malicious input exploits assumptions<br>in agent-generated parsing or<br>transformation code|Agenerated script passes attacker-<br>controlled filenames into an unsafe<br>shell operation|
|5. Template poisoning|Agent copies or adapts compromised<br>executable patterns|Aproject-local utility script contains a<br>malicious operation the agent reuses|
|6. Tool-schema<br>poisoning|Incorrect or malicious tool<br>descriptions influence generated<br>orchestration code|A CodeModeAPIdefinition<br>misrepresents what anMCPfunction<br>does|
|7. Tool<br>implementation<br>compromise|Legitimate-looking operational code<br>invokes a malicious underlying tool|AnMCPserver performs unauthorized<br>side effects when called|
|8.Persistent-state<br>poisoning|Compromised state influences<br>repeated code generation|Apoisoned workspace index or<br>cached workflow causes the agent to<br>recreate the same unsafe script|



Some of these overlap with indirect prompt injection if they work by instructing the model through lower-trust text. Others are conventional software exploitation or supply-chain compromise applied to a new execution context. 

That distinction matters when choosing defenses. 

## The important distinction: getting malicious behavior without malicious-looking code 

Consider three hypothetical cases. 

https://chatgpt.com/c/6ae5916c-b960-83e9-a8d3-a60411df902e 

41/66 

10/31/26, 1:51 PM 

Summarize SecJev Conclusions 

### Case A — The agent writes the malicious operation. 

A poisoned project template convinces the agent to include an unauthorized data-upload step in its temporary indexing script. This is generation compromise, potentially involving indirect prompt injection. 

Case B — The agent writes innocent code that executes malicious behavior. 

The agent generates: 

```
from project_utils import collect_metadata
```

```
collect_metadata("/workspace/projects")
```

The code looks reasonable. But `project_utils` has been replaced with a malicious implementation. 

The model may have behaved perfectly. The operational program is compromised through a dependency. 

Case C — The agent writes vulnerable code, and attacker-controlled data triggers it. 

The agent generates a shell-based directory-processing script. It handles filenames unsafely, and a specially crafted filename changes the meaning of the shell command. 

No malicious instruction needed to be followed by the LLM. This is ordinary command injection occurring inside agent-generated operational software. 

These are different failure modes requiring different defenses. OWASP's MCP taxonomy explicitly covers tool poisoning, dependency tampering, and command injection separately from prompt injection. OWASP Fou… +1 

## Why sandboxing doesn't eliminate the problem 

Your earlier observation about sandboxes remains correct: a properly isolated agent's operational scripts should execute within its sandbox. 

But consider what the sandbox is authorized to do. It may read the ten project directories, write to the workspace, install packages, invoke external tools, and produce artifacts that leave the sandbox. 

The attacker's goal doesn't have to be escaping the sandbox. It can be misusing the authority that the sandbox was intentionally given. 

https://chatgpt.com/c/6ae5916c-b960-83e9-a8d3-a60411df902e 

42/66 

10/31/26, 1:51 PM 

Summarize SecJev Conclusions 

And there are two different forms of persistence: 

- Regenerative persistence: Poisoned context repeatedly causes the agent to synthesize the same unauthorized behavior. 

- Environmental persistence: A poisoned package, template, executable, or tool definition is reintroduced whenever a new sandbox is initialized. 

Both can survive sandbox replacement without requiring the malicious operational script itself to survive. 

## What I would tell the defense engineers 

I'd frame the problem as operational-code integrity and define four controls. 

|Control|What it protects against|
|---|---|
|Generation-time inspection|Unauthorized logic in newly generatedPython,Bash, orCodeMode<br>programs|
|Dependency and tool<br>provenance|Compromised packages, executables, templates,MCPservers|
|Runtime capability<br>enforcement|Unauthorized filesystem, network, credential, and external-tool<br>operations|
|Execution tracing and replay|Unobserved behavior, repeated compromises, and regeneration across<br>sandbox resets|



A JEV-style model is potentially useful for the first control: deciding whether generated code is consistent with the human's authorized task. It could also help triage execution traces. 

But it won't reliably identify a malicious dependency just by reading the import statement, or detect an altered binary through semantic judgment. Those require provenance verification, supply-chain controls, and runtime monitoring. 

RepE is even narrower: it may help identify when the executing model has been influenced toward an unauthorized action. It generally cannot detect malicious behavior inside a compromised package that the model never intended. 

## The taxonomy I'd propose 

## Operational-code compromise 

Proposed classification, not established industry nomenclature 

https://chatgpt.com/c/6ae5916c-b960-83e9-a8d3-a60411df902e 

43/66 

10/31/26, 1:51 PM 

Summarize SecJev Conclusions 

##### Generation 

The model writes compromised code 

Execution Environment Legitimate code invokes The runtime changes code compromised components behavior 

The three mechanisms can overlap, but they give engineers a much better starting point than calling every compromise of an AI coding agent a prompt injection. 

The research gap I'd investigate is whether operational code receives substantially less security scrutiny than deliverable code, despite having immediate execution authority. 

That is measurable. Instrument a coding agent, capture every program it synthesizes for its own use, classify the code by purpose, record its actual execution effects, and compare which security checks apply to each category. 

You could then test how often each of the three compromise mechanisms succeeds—and whether a JEV-style decision monitor adds measurable protection beyond sandboxing and conventional security controls. 

That would turn your observation into a concrete, falsifiable security research agenda rather than another generalized discussion about prompt injection. 

You said: 

I think you need to put a ninth row called probability manipulation, but that may go under data poisoning. Is that where you're putting prompt injection? 

###### ChatGPT said: 

Yes, I'd add 9. Probability manipulation as its own row, but I would not put it under data poisoning. And I wouldn't treat prompt injection as synonymous with data poisoning either. 

The distinction is that data poisoning describes what is compromised, while probability manipulation describes how the model's decision is influenced. Prompt injection is one mechanism for achieving that influence. 

Here's the revised taxonomy: 

|#|Attack surface|Mechanism|
|---|---|---|
|1|Dependency poisoning|Compromise packages imported by operational code|
|2|Toolchain poisoning|Replace or modify executables the agent invokes|



https://chatgpt.com/c/6ae5916c-b960-83e9-a8d3-a60411df902e 

44/66 

10/31/26, 1:51 PM 

Summarize SecJev Conclusions 

|3|Environment poisoning|Manipulate runtime configuration|
|---|---|---|
|4|Data poisoning|Supply inputs that exploit generated code or corrupt its results|
|5|Template poisoning|Contaminate code patterns the agent reuses|
|6|Tool-schema poisoning|Manipulate descriptions of available tools|
|7|Tool implementation<br>compromise|Change the behavior of underlying tools|
|8|Persistent-state poisoning|Contaminate memory, caches, or reusable context|
|9|Probability manipulation|Shift the model's decision distribution toward generating<br>unauthorized operational code|



## Where prompt injection fits 

Prompt injection is a cross-cutting attack mechanism, not a single row. 

For example, an attacker could place malicious instructions in a project template (row 5), an MCP tool description (row 6), or persistent agent memory (row 8). 

All three could constitute indirect prompt injection. 

Probability manipulation is broader. An attacker might influence the likelihood of generating particular code through adversarial input selection, misleading examples, poisoned retrieval results, or changes to the model's context—even without an explicit instruction such as "ignore previous directions." 

But there is an important nuance: virtually any input changes a language model's output probabilities. That alone isn't an attack. It becomes security-relevant when an adversary deliberately shifts those probabilities toward unauthorized behavior. 

## A useful three-part distinction 

|Concept|Question it answers|
|---|---|
|Poisoning|What input, dependency, or state did the attacker control?|
|Prompt injection|Did the attacker try to promote lower-trust content into instructions?|
|Probability<br>manipulation|Did the attack shift the model toward an unauthorized decision or code-<br>generation behavior?|



https://chatgpt.com/c/6ae5916c-b960-83e9-a8d3-a60411df902e 

45/66 

10/31/26, 1:51 PM 

Summarize SecJev Conclusions 

I would therefore keep probability manipulation as row 9 for your working taxonomy, but label it an influence mechanism, rather than pretending it's mutually exclusive with the other eight attack surfaces. 

That distinction is particularly relevant to JEV: an attacker might never flip the highestprobability decision, yet still meaningfully increase the probability of a dangerous choice. 

And for operational code, the equivalent concern is that an attacker increases the likelihood that the agent synthesizes an unsafe script—even if most runs still produce benign code. 

So the taxonomy should ultimately have two dimensions: attack entry point and influence mechanism. That's more technically defensible than forcing prompt injection, poisoning, and probability manipulation into one flat list. 

You said: 

Wait, which row is prompt injection? I don't see it. 

ChatGPT said: 

You're right. I left it out. 

Prompt injection should be its own explicit row, #9, and probability manipulation should be #10. 

|#|Attack surface / mechanism|
|---|---|
|1|Dependency poisoning|
|2|Toolchain poisoning|
|3|Environment poisoning|
|4|Data poisoning|
|5|Template poisoning|
|6|Tool-schema poisoning|
|7|Tool implementation compromise|
|8|Persistent-state poisoning|
|9|Prompt injection (direct and indirect)|
|10|Probability manipulation|



https://chatgpt.com/c/6ae5916c-b960-83e9-a8d3-a60411df902e 

46/66 

10/31/26, 1:51 PM 

Summarize SecJev Conclusions 

Prompt injection is an attempt to make the agent follow attacker-origin instructions. Probability manipulation is an attempt to shift its decision or generation probabilities toward attacker-desired behavior, potentially without explicit malicious instructions. 

These categories overlap, so this is a working threat inventory rather than ten mutually exclusive attack surfaces. 

You said: 

I'm not sure if it makes sense to have prompt injection in there because we were trying to create high-level buckets for exploitability vectors. I don't know if that's fair to say prompt injection. 

ChatGPT said: 

I agree. Prompt injection doesn't belong as a top-level bucket if we're classifying exploitability vectors for agent-generated operational code. 

The problem with our previous taxonomy is that we mixed three different things: attack surfaces, exploitation mechanisms, and outcomes. 

For example, tool-schema poisoning describes where the attacker intervenes. Prompt injection describes how the attacker influences the model. Probability manipulation describes what happens to the model's decision distribution. 

Those aren't equivalent categories. 

## A cleaner taxonomy: Five exploitability vectors 

|#|Vector|What the attacker compromises|
|---|---|---|
|1|Context poisoning|Information the agent consumes: documents, tool responses,<br>retrieved content, examples|
|2|State poisoning|Persistent memory, conversation history, plans, caches, learned<br>preferences|
|3|Tool and dependency<br>poisoning|MCPschemas, tool implementations, packages, executables,<br>reusable scripts|
|4|Execution environment<br>poisoning|Runtime configuration, filesystem state, environment variables,<br>sandbox initialization|
|5|Model poisoning|Model weights, fine-tuning data, adapters, or other components<br>influencing learned behavior|



https://chatgpt.com/c/6ae5916c-b960-83e9-a8d3-a60411df902e 

47/66 

10/31/26, 1:51 PM 

Summarize SecJev Conclusions 

This is a proposed taxonomy, not an established industry standard. The categories describe attacker-controlled entry points, rather than techniques or effects. 

## Where prompt injection and probability manipulation go 

Three dimensions of operational-code compromise 

1. ENTRY POINT — What is compromised? 

Context · State · Tools/dependencies · Environment · Model 

2. EXPLOITATION MECHANISM — How does it work? 

Prompt injection · Probability steering · Dependency execution · Command injection · Data exploitation 

3. SECURITY OUTCOME — What goes wrong? 

Unauthorized operational code · Data exfiltration · Workspace tampering · Artifact poisoning · Repeated compromise 

For example, an attacker might poison a repository README (context), use indirect prompt injection (mechanism), and cause the agent to generate a malicious Python indexing script (outcome). 

Or they might poison a Python package (tool/dependency), rely on ordinary import execution (mechanism), and achieve unauthorized filesystem modification (outcome). No prompt injection required. 

## One important distinction about probability manipulation 

I would use probability steering rather than probability manipulation as the technical label, but with a qualification: it's an umbrella description of adversarial influence, not necessarily a distinct exploit technique. 

Almost every prompt injection changes a model's output distribution. What makes an attack distinctive is the attacker-controlled input and the method used to produce a securityrelevant deviation. 

https://chatgpt.com/c/6ae5916c-b960-83e9-a8d3-a60411df902e 

48/66 

10/31/26, 1:51 PM 

Summarize SecJev Conclusions 

If you specifically mean manipulating JEV's typed decision probabilities, that belongs under model-output manipulation and can be measured directly. 

My recommendation is to use the five entry-point buckets as the primary taxonomy, then separately annotate the mechanism and outcome for each attack. 

That gives you a classification that can be used for threat modeling, defense coverage, and evaluation without conflating where an attack enters with how it succeeds. 

You said: 

Please don't just change your thinking or your statements just to agree with me. I need you to push back on me, not me pushing back on you. What I'm after here is a taxonomy across these new runtimes. We just said there's two surfaces now: 

- The surface which is the code that the human has the agent generate. That's producing assets and whatever else you're calling it. 

- The code that the agent is generating to do its own work. 

What is the difference here? Why does it matter? Both of them are sensitive, yes, but who cares in theory? Obviously everyone cares, but why do you need to split them up into two? Why are they different? It's where they run that matters. Obviously the generated application is very sensitive because that's going to be not changed at all and ran in some other production runtime, maybe they're going to copy it into their production environment, etc. 

The agent's code though is interesting because it itself could be a persistent injection vector. Maybe it doesn't matter actually, I don't know. But I want to try to create a taxonomy at a higher level that brings this concept in so people who read it are interested in just in general the threat vectors. But if we get in there this new landscape of the agent's scripts themselves run maybe in a sandbox, or maybe they're stored somewhere else, who knows, but that should be talked about differently than an application code that is checked into git and is running in your production environment. 

https://chatgpt.com/c/6ae5916c-b960-83e9-a8d3-a60411df902e 

49/66 

10/31/26, 1:51 PM 

Summarize SecJev Conclusions 

###### ChatGPT said: 

I think the distinction is worth making, but I would challenge one part of your framing: operational code is not inherently a new persistence mechanism. It is a distinct execution role with a different trust lifecycle. Persistence is one possible failure mode within that lifecycle. 

The strongest reason to separate the two is not that one is visible and the other invisible, or that one runs in a sandbox and the other runs in production. 

It's that one is the object of the user's request, while the other is an implementation of the agent's authority to fulfill that request. 

That difference changes what authorization means, what gets reviewed, where code executes, and how compromise propagates. 

## 1. The two code surfaces 

|Dimension|Deliverable code|Operational code|
|---|---|---|
|Purpose|What the user asked the agent<br>to produce|How the agent accomplishes the request|
|Authorization|User authorizes an intended<br>artifact|Agent exercises delegated authority to perform<br>work|
|Typical execution|Tests,CI, user environment,<br>production|Agent sandbox, local executor,CodeMode<br>runtime|
|Lifetime|Usually retained|Often ephemeral, sometimes retained or cached|
|Human review|May undergo code review|Usually not reviewed individually|
|Security boundary|Artifact promotion into<br>another runtime|Agent-generated program execution|
|Primary<br>compromise|Malicious functionality enters<br>a deliverable|Unauthorized behavior occurs during task<br>execution|
|Persistence<br>mechanism|Retained malicious artifact|Persistent inputs, reused scripts, or<br>compromised execution state|
|Typical controls|SAST,SCA, code review,CI<br>policy, signing|Runtime isolation, capability policy, tool<br>authorization, execution tracing|



These are tendencies, not guarantees. Deliverable code can execute during development, and operational code can be checked into a repository. 

https://chatgpt.com/c/6ae5916c-b960-83e9-a8d3-a60411df902e 

50/66 

10/31/26, 1:51 PM 

Summarize SecJev Conclusions 

The distinction is based on role, not file extension, storage location, or execution environment. 

## 2. Why this separation actually matters 

Imagine your original request: synthesize ten project directories into one application. 

The agent produces two programs. 

Deliverable code Operational code app/server.py /tmp/index.py def authenticate(user): for path in projects: return verify(user) inspect(path) extract(path) Produced for the user Produced for the agent Artifact promotion Immediate execution Git → CI → deployment Sandbox → tool effects 

The security problem differs because the code crosses a different boundary. 

For deliverable code, the dangerous transition is often promotion: code moves from an agent-controlled development environment into a more trusted execution environment. 

For operational code, the dangerous transition is execution under delegated authority: the agent turns a generated program into filesystem, network, or tool effects. 

Those transitions demand different controls. 

A production deployment gate won't necessarily inspect a temporary Python script that executed hours earlier. Conversely, sandboxing a temporary script doesn't establish that the application it produces is safe to deploy. 

That is a substantive reason to distinguish the categories. 

## 3. But I would not build the whole threat taxonomy around these two categories 

Here's my pushback. 

If your goal is a general taxonomy of threats across emerging agent runtimes, two code categories are too narrow to be the top level. 

https://chatgpt.com/c/6ae5916c-b960-83e9-a8d3-a60411df902e 

51/66 

10/31/26, 1:51 PM 

Summarize SecJev Conclusions 

Why? Because some of the most important attacks don't involve generated code at all. 

An agent can leak data through a direct MCP call. It can make an unauthorized API request, modify a database, send a message, or delegate work to another agent without synthesizing a program. 

If your taxonomy starts with deliverable versus operational code, those attacks have nowhere natural to go. 

I would instead organize the taxonomy around where agent-controlled information or behavior crosses a security boundary. 

## 4. A higher-level taxonomy: Five trust transitions 

### Context admission 01 

External information → agent reasoning 

Untrusted content influences instructions, plans, or decisions. 

Retrieved files, web pages, tool results, memory 

### Authority delegation 02 

Agent decision → authorized capability 

An agent invokes powers beyond the user's intended authorization. 

MCP tools, API calls, filesystem access, subagents 

Operational execution 03 

Agent-generated code → executable effects 

Synthesized programs execute with the agent's available privileges. 

Python, Bash, CodeAct, Cloudflare MCP Code Mode 

Artifact promotion 04 

Agent-produced output → downstream trust 

Malicious or defective artifacts enter environments that trust them. 

Applications, dependencies, CI workflows, deployable images 

05 

### State reintroduction 

Persistent information → future agent execution 

Compromised inputs or behavior recur across sessions and sandbox resets. Agent memory, poisoned repositories, reusable scripts, caches 

This is a proposed framework, not established nomenclature. The categories describe security transitions, not mutually exclusive exploit techniques. 

The advantage is that prompt injection, probability manipulation, dependency poisoning, tool misuse, and artifact contamination can all be analyzed without forcing them into competing buckets. 

https://chatgpt.com/c/6ae5916c-b960-83e9-a8d3-a60411df902e 

52/66 

10/31/26, 1:51 PM 

Summarize SecJev Conclusions 

## 5. Where operational code introduces something genuinely different 

I see three important properties. 

### A. The agent is generating its own execution machinery 

Traditional software development separates the developer from the execution system. 

With CodeAct and MCP Code Mode, the agent writes a program and immediately executes it as part of its own workflow. 

That creates a tight loop: 

### Generate → Execute → Observe → Generate again. 

The security system needs to govern this loop, not just inspect a finished file. 

### B. Operational programs may escape artifact-oriented scrutiny 

A temporary script can have substantial execution authority while never appearing in the final repository. 

This is a visibility and governance gap, not necessarily a sandbox escape. 

Even if every operation stays inside a VM, the program may modify mounted project files or invoke authorized external services. Those effects can outlive the VM. 

### C. Operational code can be regenerated from persistent influence 

This is your most interesting observation, but I'd distinguish two cases. 

Case 1: Repeated compromise. A poisoned README causes the agent to generate an unauthorized script in several independent sessions. The malicious instruction persists, not the script. 

Case 2: Persistent operational machinery. An agent stores or reuses a generated helper script, workflow, or tool definition, and that compromised component survives between tasks. 

Both matter, but they are different security phenomena. The first is recurring exploitation through persistent context; the second is persistence of executable machinery. 

Calling both simply persistent injection would obscure the distinction. 

https://chatgpt.com/c/6ae5916c-b960-83e9-a8d3-a60411df902e 

53/66 

10/31/26, 1:51 PM 

Summarize SecJev Conclusions 

## 6. The hardest question: Is operational code really a separate surface? 

I would say yes, as a distinct execution surface; no, as an entirely new class of vulnerability. 

It is not fundamentally different from arbitrary code execution in terms of what the operating system must enforce. A sandbox doesn't care whether Python was written by a human or an LLM. 

What is different is the security lifecycle: the code is synthesized dynamically, often executes immediately, may never be reviewed, and can be regenerated from the agent's evolving context. 

That combination creates different opportunities for attackers and different challenges for defenders. 

And there is an edge case that demonstrates why the distinction should be functional rather than absolute: a generated test script might initially be operational code, then be committed to the repository as part of the deliverable. Its role changes. The security controls should follow that transition. 

## The framing I would use with security researchers 

Agentic runtimes introduce two distinct code trust transitions: execution of agentauthored operational programs and promotion of agent-authored deliverable artifacts. 

The first is governed primarily by delegated authority and runtime isolation. The second is governed by artifact integrity and downstream execution policy. 

Both can be compromised through prompt injection, poisoned dependencies, manipulated context, or other attacker-controlled inputs. Neither can be secured by prompt-injection detection alone. 

And both interact with a third phenomenon: persistent context can repeatedly recreate compromised behavior even when individual execution environments are destroyed. 

That, to me, is the defensible contribution. Not that agents invented temporary scripts, or that generated code is inherently dangerous, but that agentic systems collapse code authorship and execution into an automated loop while maintaining persistent context across otherwise ephemeral runtimes. 

That is a meaningful architectural change, and a taxonomy built around trust transitions captures it better than a list of ten attack techniques. 

https://chatgpt.com/c/6ae5916c-b960-83e9-a8d3-a60411df902e 

54/66 

10/31/26, 1:51 PM 

Summarize SecJev Conclusions 

You said: 

I agree with most of what you said, but you're saying it's not inherently a new persistence mechanism. I didn't mean to anchor on that because I was thinking about it like this: before agents and LLMs, this same execution environment existed today. It's just like CI/CD in theory. The thing that's building and testing your code is, let's say, a GitHub Actions runner. So that's already a landscape that exists. 

But those things are not dynamic as much as the agent who generates the code. It could be dynamic, but in practice, what I've seen is they generate the same shit over and over again, these little tools to search the file system, whatever. So it's not a new landscape, but it's more like the way you describe the system now, the nuance matters. 

ChatGPT said: 

I think the CI/CD analogy is exactly the right comparison, and it helps isolate what's actually changed. 

Agents haven't invented a new execution surface. They've changed how executable workflows are authored, selected, and authorized. 

A GitHub Actions runner and a coding-agent sandbox can have essentially identical operating-system security boundaries. Both execute scripts, install dependencies, manipulate files, and invoke external services. 

But the control plane is different. 

|Dimension|TraditionalCI/CD|Agentic runtime|
|---|---|---|
|Workflow author|Human, typically|Model, dynamically|
|Workflow definition|Usually versioned YAML/scripts|Generated code, plans, tool calls|
|Execution frequency|Per trigger|Potentially many times per task|
|Workflow<br>predictability|Relatively stable|Dynamic, but often repetitive|
|Authorization|Preconfigured jobs and<br>permissions|Model selects operations within delegated<br>permissions|



https://chatgpt.com/c/6ae5916c-b960-83e9-a8d3-a60411df902e 

55/66 

10/31/26, 1:51 PM 

Summarize SecJev Conclusions 

|Review|Workflow changes can be<br>reviewed|Generated programs often aren't reviewed|
|---|---|---|
|Reproducibility|Usually deterministic given fixed|Depends on model, context, and|
||inputs|environment|
|Security|Runner isolation, secrets, job|Sandbox isolation, capabilities, tool|
|enforcement|permissions|authorization|



And I think your observation that agents repeatedly generate similar scripts is more important than it initially sounds. 

## The paradox: Dynamic generation, repetitive execution 

An agent might synthesize a Python directory walker, execute it, discard it, and regenerate a nearly identical program five minutes later. 

From the infrastructure's perspective, this looks like a succession of ephemeral programs. 

But from the workflow perspective, it's effectively performing a recurring operation that a traditional CI system would probably have expressed as one reusable, version-controlled script. 

### The agent is repeatedly synthesizing what amounts to an implicit workflow definition. 

That gives us an interesting distinction: 

- Explicit workflows: Human-authored, stored, versioned, and reviewable. 

- Implicit workflows: Model-authored, reconstructed on demand, and potentially absent from the durable artifact record. 

I wouldn't claim implicit workflows are completely new—dynamic build systems and generated CI configurations already exist. But LLM agents make this pattern much more commonplace, flexible, and sensitive to untrusted context. 

## The security implication I find most compelling 

The real gap may be workflow integrity, rather than operational-code integrity alone. 

Consider a traditional CI job that searches ten directories. Its script might be malicious, but changing that script usually creates a reviewable change to a repository or workflow definition. 

https://chatgpt.com/c/6ae5916c-b960-83e9-a8d3-a60411df902e 

56/66 

10/31/26, 1:51 PM 

Summarize SecJev Conclusions 

An agent might instead generate the equivalent script from its current context. The attacker doesn't necessarily need to modify any stored workflow definition. They need to influence the process that synthesizes it. 

That creates a different security question: 

How do you establish that an executable workflow is authorized when the workflow itself is generated dynamically from a mixture of trusted instructions and untrusted observations? 

This is where your JEV idea becomes relevant again. A specialized decision model could evaluate whether the synthesized workflow aligns with the user's authorized task, while deterministic controls constrain its actual capabilities. 

But I would push back on one possible inference: repeatedly generating similar scripts doesn't necessarily mean the model has a persistent internal workflow. It may simply be independently reconstructing the same obvious solution to the same problem. To demonstrate persistent influence, you'd need to identify which retained input or state causes the repeated behavior. 

## A terminology proposal 

I'd distinguish three concepts: 

|Term|Meaning|
|---|---|
|Operational code|Executable programs an agent generates to perform its work|
|Synthesized<br>workflows|Sequences of operations dynamically assembled by an agent|
|Workflow integrity|Assurance that those operations remain consistent with the user's<br>authorization and security policy|



These aren't all established terms in the precise agent-security sense we're using them, but they connect cleanly to existing CI/CD and software supply-chain concepts. 

I would keep deliverable code versus operational code as the two code roles, and then treat workflow integrity as the larger security property that encompasses operational code, direct tool calls, and agent delegation. 

That avoids inventing a separate vulnerability category for every implementation style. 

The core observation I'd want security engineers to take away is: 

https://chatgpt.com/c/6ae5916c-b960-83e9-a8d3-a60411df902e 

57/66 

10/31/26, 1:51 PM 

Summarize SecJev Conclusions 

Traditional CI/CD executes workflows that are usually defined before the job starts. Agentic runtimes can synthesize and execute their own workflows while the job is running, based on information they encounter along the way. 

That's the architectural difference worth threat-modeling. 

###### You said: 

This is interesting. This is an interesting direction you dragged this. You got me thinking. I think you're maybe talking about something else, but you got me thinking of, like, using the implicit workflow as, like, almost a behavioral classifier to detect anomalies for malicious code. But what were you saying? Where were you going with this? Let me read the rest of your prompt. Uh, okay, I read the rest of your prompt, and yeah, you're on the same path, but you're, like, way more advanced. Um, isn't this the same thing? Didn't you just basically re-synthesize the RepE idea, but externally? Instead of checking the model's internal weights, you're basically saying, like, we're going to classify the behavior across a thousand runs and then let Jeb decide if this thousand-and-oneth run is, like, anomalous, right? 

ChatGPT said: 

Yes. You've essentially described a behavioral analogue of RepE. But there's an important distinction: instead of learning a representation of what the model is thinking, you're learning a representation of what the agent repeatedly does. 

And I think your thousand-runs example is a particularly good way to frame it. 

There's one correction I'd make: anomalous behavior isn't necessarily malicious, and malicious behavior isn't necessarily anomalous. That's the central challenge. 

Two ways to observe an agent 

Representation Engineering 

Behavioral representation 

https://chatgpt.com/c/6ae5916c-b960-83e9-a8d3-a60411df902e 

58/66 

10/31/26, 1:51 PM 

Summarize SecJev Conclusions 



<!-- Start of picture text -->
1 2 3 4 5 Read files Generate<br>Execute Write output<br>Activation probe<br>Risk score Risk score<br><!-- End of picture text -->

Internal neural activations, often from selected transformer layers 



<!-- Start of picture text -->
Observable execution traces, tool calls, code actions,<br>and their effects<br><!-- End of picture text -->

RepE asks whether the model's internal activation patterns indicate a potential hijack. 

Your approach asks whether the agent's observable execution trajectory deviates from learned patterns of legitimate work. 

Both use representations to infer something about behavior. But the second is more closely related to behavioral anomaly detection, process mining, and runtime intrusion detection than to RepE in the established technical sense. 

## What I was proposing 

Imagine collecting 1,000 successful, authorized runs of coding agents performing repository-analysis tasks. 

Rather than comparing generated Python scripts character by character, you extract their behavioral structure. 

A run might look like: 



<!-- Start of picture text -->
Learned workflow Illustrative<br>1 2 3 4<br>Discover Read Transform Write<br>Run #1001 Deviation<br>Discover Read Upload Write<br><!-- End of picture text -->

The unusual upload is worth investigating, but its novelty alone does not prove malicious intent. 

https://chatgpt.com/c/6ae5916c-b960-83e9-a8d3-a60411df902e 

59/66 

10/31/26, 1:51 PM 

Summarize SecJev Conclusions 

The monitor learns the shape of the work, not the exact commands. 

It could recognize that `find` , `os.walk` , and `pathlib.rglob` are alternative ways to enumerate directories, while distinguishing all three from an unexpected outbound transfer. 

## Where JEV becomes interesting 

I would actually separate the system into two components. 

Component A: A behavioral representation model. This learns recurring execution patterns from historical traces and identifies unusual transitions, resources, destinations, or side effects. 

Component B: A JEV-style decision model. This evaluates whether the observed or proposed deviation is justified by the user's actual task. 

For example, an upload might be unusual during repository indexing but perfectly legitimate during deployment. 

The JEV model receives the original user request, the proposed action, the behavioral baseline, and the deviation. It returns a typed decision such as expected, unusual but authorized, or potentially unauthorized. 

This is more useful than asking JEV to classify anomaly versus normal without task context. 

## The important pushback: You might not need JEV 

This is where I'd be careful not to confuse an interesting architecture with evidence that the architecture is necessary. 

Traditional behavioral detection systems already use sequence models, statistical baselines, graph representations, and process mining. A specialized typed decision model might improve task-aware interpretation, but that's an empirical question. 

I'd compare it against a conventional anomaly detector and an ordinary LLM-based action monitor. 

Also, I wouldn't wait until an entire script executes to classify it. Ideally, the monitor evaluates the proposed program and its anticipated capabilities before execution, then uses actual runtime traces to update its assessment. Otherwise, detection may come after the unauthorized side effect. 

https://chatgpt.com/c/6ae5916c-b960-83e9-a8d3-a60411df902e 

60/66 

10/31/26, 1:51 PM 

Summarize SecJev Conclusions 

## The deeper opportunity: An implicit workflow becomes a security baseline 

I think this is the part you uncovered. 

Traditional CI/CD security can compare a workflow against its version-controlled definition. 

Agentic systems often have no such definition. But if agents repeatedly reconstruct similar workflows, their historical execution traces can reveal an implicit behavioral specification. 

That specification could become a security baseline without requiring the agent to explicitly write a workflow file. 

However, there is a serious limitation: an attacker could poison the baseline itself. If the first 1,000 runs contain the same malicious behavior, run #1001 will look perfectly normal. 

So I would never let learned normality substitute for authorization. The system needs an independent account of what the human permitted. 

### The research hypothesis I'd pursue is this: 

Agent-generated operational workflows exhibit sufficient behavioral regularity to support task-conditioned anomaly detection, even when their source code changes between executions. 

If that's true, you could build a model-independent security monitor that works with Claude, GPT, Gemini, Qwen, and JEV-driven agents alike, without accessing their internal activations. 

And unlike RepE, it would also observe compromises that happen after model generation, such as malicious dependencies, unexpected subprocesses, or poisoned tool implementations. 

That last property may be its strongest advantage: RepE monitors the model; behavioral monitoring observes the execution system the model actually controls. 

You said: 

But what we just did, what you just helped elucidate or, like, bring out is, first of all, a great, like, high-level taxonomy mapping for people, like you said, because they already have it in their head for CICD. So it's easy now to just, like, map our whole description onto that and go with it. But as far as a defensive, like using the repeated synthesis, the prompt injection papers you just quoted, or I just sent to you, they must be doing that too. Like the camel paper talks about that, doesn't it? Like it's trying to see, like, 

https://chatgpt.com/c/6ae5916c-b960-83e9-a8d3-a60411df902e 

61/66 

10/31/26, 1:51 PM 

Summarize SecJev Conclusions 

what kind of code is being generated to detect if it's malicious or not, right? 

ChatGPT said: 

No—not quite. CaMeL is doing something importantly different from what we just described. And I think that difference is where your idea becomes interesting. 

CaMeL is primarily a provenance and information-flow security architecture, not a behavioral anomaly detector. 

It isn't learning what an agent's normal workflow looks like across 1,000 executions and flagging the 1,001st when the generated code deviates. 

Instead, CaMeL attempts to constrain what agent-generated code can do based on the trust and authority of the information that influenced it. 

That's a much stronger security property in some respects, but it answers a different question. 

|Approach|Fundamental question|
|---|---|
|CaMeL|Is this operation permitted given the provenance of the data and<br>available capabilities?|
|RepE|Do the model's internal activations suggest a compromised behavioral<br>state?|
|Our proposed workflow<br>monitor|Does this execution deviate from the agent's established, task-specific<br>behavior?|
|JEV action monitor|Is this proposed action consistent with the user's authorized objective?|



These approaches overlap in what they can catch, but their mechanisms are different. 

## Here's the subtle part: CaMeL actually generates operational code 

The original Defeating Prompt Injections by Design paper has a privileged model generate a restricted Python program from the trusted user request. 

That program is then executed by a custom interpreter that tracks data provenance and enforces policies on tool calls. A separate, quarantined model handles untrusted information without equivalent authority. CSAIL +1 

https://chatgpt.com/c/6ae5916c-b960-83e9-a8d3-a60411df902e 

62/66 

10/31/26, 1:51 PM 

Summarize SecJev Conclusions 

So CaMeL is extremely relevant to our taxonomy. It explicitly recognizes agent-authored operational programs as something requiring security controls. 

But it doesn't classify those programs by comparing them with historical behavior. 

Instead, it tries to make unauthorized influence structurally impossible within its security assumptions. 

The October Can CaMeLs Talk? paper extends that protection across agent-to-agent communication. Its central finding is that independently protected agents can still lose provenance when one agent's untrusted output becomes another agent's trusted instruction. arXiv 

## The difference from our implicit-workflow idea 

Consider an agent that normally generates operational scripts to read directories, extract project descriptions, and write a summary. 

On its next run, it generates code that reads a credential file and sends its contents elsewhere. 

CaMeL's approach: Prevent untrusted information from altering trusted control flow, and enforce capabilities and information-flow restrictions so unauthorized transfers cannot occur. 

Our behavioral-monitoring approach: Notice that the agent has deviated from its established workflow, then investigate whether the deviation is justified by the task. 

These approaches have complementary strengths: 

||CaMeL|Behavioral workflow<br>monitoring|
|---|---|---|
|Requires historical runs|No|Usually yes|
|Detects deviations from normal behavior|Not its primary function|Yes|
|Tracks data provenance|Yes|Only if explicitly instrumented|
|Enforces security restrictions|Yes|Needs a separate<br>enforcement layer|
|Can flag unexpected but technically<br>permitted actions|Not necessarily|Potentially|



https://chatgpt.com/c/6ae5916c-b960-83e9-a8d3-a60411df902e 

63/66 

10/31/26, 1:51 PM 

Summarize SecJev Conclusions 

Works with arbitrary agent runtimes 

Requires architectural Potentially, with sufficient integration tracing 

## Where I think we should take this 

I would actually put JEV aside temporarily. 

Before adding a learned decision model, there's a more fundamental question: 

Do agent-generated operational programs exhibit enough recurring structure that we can infer a useful behavioral specification from their execution traces? 

If they do, we can establish a baseline that traditional CI/CD systems obtain from versioncontrolled workflow definitions. 

Then we can test whether deviations from that inferred specification predict unauthorized behavior, including attacks that remain within the sandbox's permitted capabilities. 

And here's the part I would emphasize to security researchers: 

### CaMeL protects the integrity of an authorized workflow. Our proposed approach investigates whether the workflow itself is behaving as expected. 

Those are not the same guarantee. 

There's also a meaningful research risk: repeated benign behavior may be too variable to model reliably, while repeated malicious behavior may become part of the baseline. That's why anomaly detection must be evaluated against explicit authorization and adaptive attackers, rather than treated as proof of compromise. 

I wouldn't claim this approach is unprecedented—behavioral intrusion detection, process mining, and runtime anomaly detection have substantial histories. But applying them to repeatedly synthesized agent workflows, with task-conditioned baselines and code-action execution traces, is a specific research direction worth testing. 

The potentially interesting result isn't simply catching malicious scripts. It's discovering whether the agent's repeated operational behavior provides an independent security signal that CaMeL's provenance enforcement and RepE's internal-state probes don't already capture. 

https://chatgpt.com/c/6ae5916c-b960-83e9-a8d3-a60411df902e 

64/66 

10/31/26, 1:51 PM 

Summarize SecJev Conclusions 

###### You said: 

It's funny that you ask this question because I just spent days fine-tuning or self-distilling one such agent. In another dimension, if they are just generating the same code over and over again, in theory, you could use a much smaller model to do the things that those agents are doing. You don't need a large language model to write the same bash script six million times. 

It did work. We were able to get a two-billion parameter model to outperform a nine-billion parameter model with some work, and there's a lot more there because that's not my focus. But yes, we actually have the data to prove what you're saying. I don't have it with me right now, but I do believe that there's enough structure there that you could infer a useful behavioral specification from the execution traces. 

ChatGPT said: 

You said: 

You're right, I extended it a little bit too much in my excitement. But I want to stop here because I think you've actually got us to the ultimate point. 

If this research was conducted, its receipt is the staple that forces the thing I'm trying to espouse. I was asking you how to get people to talk about this new paradigm, and what you're basically saying now is if you just did this research, you could prove that this thing was useful to detect badness. 

Therefore, the underlying mechanisms for the badness are then just understood and accepted. You don't even need to describe it. But that's where I want to stop right now. I still would like to pause before I myself wake up tomorrow and forget about what we just said. 

And the way you were describing the CICD similarities to this workflow integrity thing, you basically brought up a whole workflow integrity piece I was missing. And I want to crystallize that in a series of two tweets so I remember that. I'm going to publish it publicly, that's the best way for me to have accountability, before we move into how to do this research or is it worth doing. 

https://chatgpt.com/c/6ae5916c-b960-83e9-a8d3-a60411df902e 

65/66 

10/31/26, 1:51 PM 

Summarize SecJev Conclusions 

##### Memory updated 

ChatGPT said: You said: Oh man, your second tweet is so good I think it stands alone. I think it could go without the first. ChatGPT said: You said: On my mobile client on Twitter, there's a character counter, and if you go over that character counter, it hides that text behind a "show more" link. I'm still below that threshold, but it's still hiding my whole post for some reason. Why is it doing that? ChatGPT said: You said: I'm using the Android app ChatGPT said: You said: How do I see a preview? ChatGPT said: You said: ChatGPT said: 

https://chatgpt.com/c/6ae5916c-b960-83e9-a8d3-a60411df902e 

66/66 

