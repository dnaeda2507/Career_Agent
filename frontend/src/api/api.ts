export interface ApiResponse {
  response: string;
  is_revised: boolean;
  evaluation_log: any;
}

export const sendMessageToAgent = async (
  userId: string,
  message: string
): Promise<ApiResponse> => {
  const res = await fetch("http://localhost:8000/career-agent", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      user_id: userId,
      message: message,
    }),
  });

  if (!res.ok) {
    throw new Error("API error");
  }

  return res.json();
};

export const getConversation = async (userId: string) => {
  const res = await fetch(
    `http://localhost:8000/conversation/${userId}`
  );

  if (!res.ok) {
    throw new Error("Failed to fetch conversation");
  }

  return res.json();
};