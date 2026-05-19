// Demo build has no roles — there are no admin-gated pages here.
// Kept as a stub so any inherited consumer code still resolves.

export const useInternalCheck = () => {
  const checkIsInternal = async (): Promise<boolean> => false;
  return { checkIsInternal };
};
