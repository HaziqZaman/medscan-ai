export async function runAnalysis(imageFile) {

  const formData = new FormData();
  formData.append("file", imageFile);

  const response = await fetch("http://127.0.0.1:8000/predict", {
    method: "POST",
    body: formData
  });

  return await response.json();
}