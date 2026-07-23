import toast from "react-hot-toast";

export const AlertService = {
  success: (message: string) => {
    toast.success(message, {
      duration: 4000,
      position: "top-right",
      style: {
        background: '#10B981', // Verde de éxito
        color: '#fff',
      },
    });
  },
  
  error: (message: string) => {
    toast.error(message, {
      duration: 5000,
      position: "top-right",
      style: {
        background: '#EF4444', // Rojo de error
        color: '#fff',
      },
    });
  },

  info: (message: string) => {
    toast(message, {
      duration: 3000,
      position: "top-right",
      style: {
        background: '#3B82F6', // Azul de información
        color: '#fff',
      },
    });
  }
};