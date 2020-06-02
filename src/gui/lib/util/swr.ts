/**
 * Utility functions to work with Zeit's SWR hook
 */

type IdObject = Required<{ id: any }>;

/**
 * Given a list of objects (`objectList`) that have a unique `id` attribute, as well as a single
 * object `newObject` with an `id` attribute:
 *
 * * Appends `newObject` to `objectList` if an object with an equal `id` does not yet exists
 * * Replaces any object `x` in `objectList` which has `x.id == newObject.id` with `newObject`
 *
 * @returns The updated version of `objectList`
 */
export function updateObjectListById<T extends IdObject>(objectList: T[], newObject: T) {
  if (objectList == null) {
    return null;
  }

  let isReplaced = false;
  const updatedObjectList = objectList.filter((current) => {
    if (current.id === newObject.id) {
      isReplaced = true;
      return newObject;
    } else {
      return current;
    }
  });

  if (isReplaced) {
    return updatedObjectList;
  } else {
    objectList.push(newObject);
    return objectList;
  }
}

/**
 * Given a list of objects (`objectList`) that contains an `id` property, invokes the provided
 * `mutator` function on the object with the provided `id` and returns a modified version of
 * `objectList` where the object that has the provided `id` value is replaced by the return value of
 * the `mutator` function.
 */
export function updateObjectsListItemById<T extends IdObject>(
  objectList: T[],
  id: any,
  mutator: (object: T) => T
) {
  return objectList.map((item) => (item.id === id ? mutator(item) : item));
}
