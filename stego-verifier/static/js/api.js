// Thin wrappers around fetch that turn API errors into readable messages.

const GENERIC_ERROR = "Something went wrong. Please try again.";

export async function postForm(url, formData) {
  const response = await fetch(url, { method: "POST", body: formData });
  if (!response.ok) {
    throw new Error(await readErrorMessage(response));
  }
  return response.json();
}

export function buildFormData(fields) {
  const formData = new FormData();
  Object.entries(fields).forEach(([name, value]) => formData.append(name, value));
  return formData;
}

async function readErrorMessage(response) {
  try {
    const body = await response.json();
    return describeErrorDetail(body.detail);
  } catch {
    return GENERIC_ERROR;
  }
}

function describeErrorDetail(detail) {
  if (typeof detail === "string") {
    return detail;
  }
  if (Array.isArray(detail) && detail.length > 0) {
    return detail.map((item) => item.msg).join("; ");
  }
  return GENERIC_ERROR;
}
