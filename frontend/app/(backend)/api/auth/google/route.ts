import { NextRequest, NextResponse } from "next/server";
import { OAuth2Client } from "google-auth-library";

export async function POST(req: NextRequest) {
    try {
        const { id_token } = await req.json();

        if (!id_token) {
            return NextResponse.json(
                { error: "id token is required" },
                { status: 400 }
            );
        }
        const googleClientId = process.env.NEXT_PUBLIC_GOOGLE_OAUTH_CLIENT_ID;
        if (!googleClientId) {
            return NextResponse.json(
                { error: "google oauth not configured" },
                { status: 500 }
            );
        }

        // verify the google id token
        const client = new OAuth2Client(googleClientId);
        let ticket;
        try {
            ticket = await client.verifyIdToken({
                idToken: id_token,
                audience: googleClientId,
            });
        } catch (error: any) {
            console.error("error verifying google id token:", error);
            return NextResponse.json(
                { error: "invalid google token" },
                { status: 400 }
            );
        }

        // extract user information from the verified token
        const payload = ticket.getPayload();
        if (!payload) {
            return NextResponse.json(
                { error: "failed to extract user information" },
                { status: 400 }
            );
        }
        // get user information from the payload
        const googleId = payload.sub;
        const email = payload.email;
        const name = payload.name;
        const picture = payload.picture;
        const emailVerified = payload.email_verified || false;

        if (!email) {
            return NextResponse.json(
                { error: "Email not provided by Google" },
                { status: 400 }
            );
        }

        // send verified user data to python backend
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
        const backendResponse = await fetch(`${apiUrl}/users/auth/google`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                google_id: googleId,
                email: email,
                name: name,
                picture: picture,
                email_verified: emailVerified,
            }),
        });

        if (!backendResponse.ok) {
            const errorData = await backendResponse.json().catch(() => ({}));
            return NextResponse.json(
                { error: errorData.detail || "backend authentication failed" },
                { status: backendResponse.status }
            );
        }

        const userData = await backendResponse.json();
        return NextResponse.json(userData, { status: 200 });
    } catch (error: any) {
        console.error("error in google oauth api route:", error);
        return NextResponse.json(
            { error: error.message || "internal server error" },
            { status: 500 }
        );
    }
}

