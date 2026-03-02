[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/Nt4zUlkt)

# Final Project: Research, Implementation, and Defense against HTTP Request Smuggling (Track A)

## Introduction
This project focuses on an in-depth analysis of HTTP traffic and the exploitation of web routing mechanisms. The goal is to practically demonstrate how a desynchronization between front-end servers (Proxies/Load Balancers) and back-end application servers leads to the **HTTP Request Smuggling** vulnerability. Furthermore, it explores how modern defense mechanisms handle escalation attempts.

## 1. Theoretical Background and Vulnerability Explanation
In modern web architectures, client requests often pass through edge components (like Reverse Proxies or WAFs) before reaching the application server. To optimize communication, these servers use the HTTP Keep-Alive mechanism, which allows multiple HTTP requests to be sent over a single, persistent TCP connection.

For servers to determine where one request ends and the next begins, the HTTP/1.1 protocol provides two primary methods for specifying the request body length:
* **`Content-Length` (CL):** Explicitly specifies the size of the request body in bytes.
* **`Transfer-Encoding: chunked` (TE):** Transmits data in chunks, ending with a final chunk of size `0`.



**The Vulnerability (CL.TE):**
The vulnerability occurs when an attacker sends an ambiguous request containing *both* headers. The front-end server interprets the request using the `Content-Length` header and forwards the entire payload. In contrast, the back-end server uses the `Transfer-Encoding` header, reads the terminating `0` chunk, and assumes the request is complete. As a result, the remaining malicious payload sent by the attacker is left "hanging" in the back-end server's buffer, waiting to be prepended to the next legitimate request sent over the same connection.

## 2. Lab Environment
To research this vulnerability, a vulnerable local practice environment was built using Docker Compose:
* **Frontend:** HAProxy (version 1.9), configured to forward connections while aggressively reusing TCP connections (`http-reuse always`). It also acts as a basic WAF, blocking direct access to the `/admin` path.
* **Backend:** A Python/Flask web application running on Gunicorn (using older versions that do not strictly normalize headers), configured to support Keep-Alive and prioritize the `Transfer-Encoding` header.

## 3. Proof of Concept (POC) - Request Poisoning
In the first stage, we proved the existence of the desynchronization by poisoning an innocent user's request.

Using a Python script that interacts directly with a TCP socket, the following malicious request was sent:

```http
POST / HTTP/1.1
Host: 127.0.0.1
Connection: keep-alive
Content-Length: 6
Transfer-Encoding: chunked

0

G

The Frontend forwarded the entire block (6 bytes). The Backend read the 0, terminated the request processing, and left the letter G in the buffer.
When a victim sent a legitimate GET / HTTP/1.1 request immediately afterward on the same connection, the back-end server appended the G, interpreting the request as GGET / HTTP/1.1.
Result: The server returned a 405 Method Not Allowed error to the victim, successfully proving that one user's traffic can directly compromise another's.

Exploit Output - Demonstrating the victim receiving a 405 error:

Frontend (HAProxy) Logs - Proving the letter 'G' was prepended to the victim's request:

4. Advanced Research: Escalation Attempts and Real-World Defenses
After establishing the baseline vulnerability, the research focused on escalating the attack—attempting to bypass the Frontend's Access Control (WAF) to extract sensitive data from the restricted /admin route. This stage revealed how modern defenses handle network anomalies.

Attempt 1: Smuggling a Complete Request (Access Control Bypass)
We attempted to smuggle a complete POST /admin request within the body of a legitimate request, aiming to "absorb" the victim's request and return the sensitive data.

Result: HAProxy identified the internal request, triggered its ACL rules, and blocked the attack with a 403 Forbidden error. This demonstrates that even during desynchronization, the proxy continues to inspect traffic streams.

Attempt 2: Header Obfuscation
To bypass HAProxy's detection, we attempted to "dirty" the Transfer-Encoding header using special characters (e.g., a space before the colon Transfer-Encoding : chunked, or a vertical tab \x0b), hoping the Frontend would ignore it while the Backend would normalize it.

Result: HAProxy triggered its Strict HTTP Parsing mechanism. Realizing the request violated the RFC 7230 standard (which forbids spaces or control characters in headers), it completely rejected the request with a 400 Bad Request error and immediately closed the TCP connection.

5. Conclusions and Prevention
The experiments in this project highlight the critical importance of Defense in Depth. While the desynchronization vulnerability exists, successfully exploiting it in the real world requires bypassing strict security mechanisms.

To completely prevent HTTP Request Smuggling, the following steps should be taken:

End-to-End HTTP/2: Using HTTP/2 eliminates this class of vulnerabilities, as it uses robust binary framing to determine request lengths rather than conflicting text-based headers.

Upgrading Backend Servers: Modern web servers (like recent versions of Gunicorn) automatically close TCP connections when they detect conflicting headers or suspect smuggled payloads.

Enforcing Strict Routing & Parsing: Configuring WAFs and Frontend proxies to outright reject any ambiguous requests (containing both TE and CL) with a 400 Bad Request error before they ever reach the internal network.
